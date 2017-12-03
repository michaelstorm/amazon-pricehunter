import bottlenose
import os
import time
import xml.dom.minidom as xml_minidom

from io import StringIO
from urllib.error import HTTPError
from xml.etree import ElementTree as ET


sleep_time = 1.5
print_xml = False
last_pretty_xml = None
ignore_exceptions = False


def do_amazon_api_call(aws_credentials_index, Action, call_args):
    time.sleep(sleep_time)

    access_key_id = os.environ.get('AWS_ACCESS_KEY_ID_{}'.format(aws_credentials_index))
    secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY_{}'.format(aws_credentials_index))
    store_id = os.environ.get('AWS_STORE_ID_{}'.format(aws_credentials_index))

    amazon = bottlenose.Amazon(access_key_id, secret_access_key, store_id)

    print(', '.join([aws_credentials_index, Action, str(call_args)]))
    function = getattr(amazon, Action)
    response_data = function(**call_args).decode('utf-8')
    return response_data


def parse_xml_to_doc(xml_string):
    return ET.parse(StringIO(xml_string))


def pretty_print_xml(xml_string):
    return xml_minidom.parseString(xml_string).toprettyxml()


def amazon_api_call(aws_credentials_index, Action, **call_args):
    retries_remaining = 100

    while True:
        try:
            xml_string = do_amazon_api_call(aws_credentials_index, Action, call_args)

            global last_pretty_xml
            last_pretty_xml = pretty_print_xml(xml_string)

            if print_xml:
                print(last_pretty_xml)

            return parse_xml_to_doc(xml_string), xml_string

        except HTTPError as e:
            if e.code == 503 and retries_remaining > 0:
                retries_remaining -= 1
                print('Rate limited exceeded; retrying')
            elif not ignore_exceptions:
                print("Error: {}".format(str(e)))
                # raise HTTPError causes Celery to think the error came from the broker, so wrap it
                # in something else
                raise Exception(e)

        except Exception as e:
            if ignore_exceptions:
                print('Exception in query:', str(e))
            else:
                raise e
