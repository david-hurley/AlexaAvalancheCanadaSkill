# -*- coding: utf-8 -*-

# This is a Color Picker Alexa Skill.
# The skill serves as a simple sample on how to use  
# session attributes.

import logging

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
# from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.services.directive import (
    SendDirectiveRequest, Header, SpeakDirective)
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient
import requests
import json
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup

skill_name = "Avalanche Forecast Briefing"
help_text = ("Say a location and I will provide your Avalanche Canada Forecast. You can say "
             "give me the avalanche forecast for Lake Louise Alberta. Or "
             "what is the forecast for Whistler BC. Or "
             "what is the avalanche summary for Mount Revelstoke British Columbia.")

location_slot = "Location"

sb = CustomSkillBuilder(api_client=DefaultApiClient())

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""
    # type: (HandlerInput) -> Response
    speech = "Welcome to the Alexa Avalanche Canada daily forecast briefing."

    handler_input.response_builder.speak(
        speech + " " + help_text).ask(help_text)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    handler_input.response_builder.speak(help_text).ask(help_text)
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "Goodbye and be safe!"

    return handler_input.response_builder.speak(speech_text).response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    # type: (HandlerInput) -> Response
    return handler_input.response_builder.response

def get_progressive_response(handler_input):
    # type: (HandlerInput) -> None
    request_id_holder = handler_input.request_envelope.request.request_id
    directive_header = Header(request_id=request_id_holder)
    speech = SpeakDirective(speech="Give me a minute while I retrieve your forecast.")
    directive_request = SendDirectiveRequest(
        header=directive_header, directive=speech)

    directive_service_client = handler_input.service_client_factory.get_directive_service()
    directive_service_client.enqueue(directive_request)
    return

@sb.request_handler(can_handle_func=is_intent_name("MyLocationIsIntent"))
def my_color_handler(handler_input):
    """Check if location is provided in slot values. If provided, then
    set your location and send request to avalanche canada endpoint.
    """

    get_progressive_response(handler_input)

    # type: (HandlerInput) -> Response
    slots = handler_input.request_envelope.request.intent.slots

    if location_slot in slots:
        my_location = slots[location_slot].value

        locator = Nominatim(user_agent='myGeocoder')
        location = locator.geocode(my_location, country_codes='ca')

        url = "https://api.avalanche.ca/forecasts/:lang/products/point?lat={}&long={}".format(location.latitude, location.longitude)

        resp = requests.get(url)

        json_data = json.loads(resp.text)

        rating_date = json_data['report']['dangerRatings'][0]['date']['display']
        rating_alpine = json_data['report']['dangerRatings'][0]['ratings']['alp']['rating']['display']
        rating_treeline = json_data['report']['dangerRatings'][0]['ratings']['tln']['rating']['display']
        rating_belowtreeline = json_data['report']['dangerRatings'][0]['ratings']['btl']['rating']['display']

        ratings_summary = 'The danger rating for today, {}, is the following. Alpine is {}, treeline is {}, and below treeline is {}.'.format(rating_date, rating_alpine, rating_treeline, rating_belowtreeline)

        avy_main = json_data['report']['highlights']
        avy_summary = json_data['report']['summaries'][0]['content']
        avy_snowpack = json_data['report']['summaries'][1]['content']
        avy_weather = json_data['report']['summaries'][2]['content']

        l = [
            avy_main, 
            ratings_summary, 
            'Here is the detailed avalanche summary.',
            avy_summary, 
            'Here is the detailed snowpack summary.',
            avy_snowpack, 
            'Here is the detailed weather summary.',
            avy_weather
        ]

        clean_string = []
        for txt in l:
            soup = BeautifulSoup(txt, 'html.parser')
            clean_string.append(soup.get_text(' ', strip=True))

        clean_string = ' '.join(clean_string)

        speech = ("Warning: this briefing does not replace the Avalanche Canada web app or mobile app. Verify all information at avalanche.ca. "
                  "Here is the Avalanche Canada summary for {}. "
                  "{}".format(my_location, clean_string))
    else:
        speech = ("I can't seem to find a location matching that name inside the Avalanche Canada dynamic region boundaries. "
                  "Please provide a new location within the dynamic region boundaries.")

    handler_input.response_builder.speak(speech)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    # type: (HandlerInput) -> Response
    speech = (
        "The {} skill can't help you with that.  "
        "You can request a avalanche forecast summary by saying "
        "give me the avalanche forecast for Lake Louise Alberta").format(skill_name)
    handler_input.response_builder.speak(speech)
    return handler_input.response_builder.response


def convert_speech_to_text(ssml_speech):
    """convert ssml speech to text, by removing html tags."""
    # type: (str) -> str
    s = SSMLStripper()
    s.feed(ssml_speech)
    return s.get_data()


@sb.global_response_interceptor()
def add_card(handler_input, response):
    """Add a card by translating ssml text to card content."""
    # type: (HandlerInput, Response) -> None
    response.card = SimpleCard(
        title=skill_name,
        content=convert_speech_to_text(response.output_speech.ssml))


@sb.global_response_interceptor()
def log_response(handler_input, response):
    """Log response from alexa service."""
    # type: (HandlerInput, Response) -> None
    print("Alexa Response: {}\n".format(response))


@sb.global_request_interceptor()
def log_request(handler_input):
    """Log request to alexa service."""
    # type: (HandlerInput) -> None
    print("Alexa Request: {}\n".format(handler_input.request_envelope.request))


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    # type: (HandlerInput, Exception) -> None
    print("Encountered following exception: {}".format(exception))

    speech = "Sorry, there was some problem. Please try again!!"
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


######## Convert SSML to Card text ############
# This is for automatic conversion of ssml to text content on simple card
# You can create your own simple cards for each response, if this is not
# what you want to use.

from six import PY2
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser


class SSMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.full_str_list = []
        if not PY2:
            self.strict = False
            self.convert_charrefs = True

    def handle_data(self, d):
        self.full_str_list.append(d)

    def get_data(self):
        return ''.join(self.full_str_list)

################################################


# Handler to be provided in lambda console.
lambda_handler = sb.lambda_handler()