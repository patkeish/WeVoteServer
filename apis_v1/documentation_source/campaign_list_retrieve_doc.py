# apis_v1/documentation_source/campaign_list_retrieve_doc.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-


def campaign_list_retrieve_doc_template_values(url_root):
    """
    Show documentation about campaignListRetrieve (No CDN)
    """
    required_query_parameter_list = [
        {
            'name':         'voter_device_id',
            'value':        'string',  # boolean, integer, long, string
            'description':  'An 88 character unique identifier linked to a voter record on the server',
        },
        {
            'name':         'api_key',
            'value':        'string (from post, cookie, or get (in that order))',  # boolean, integer, long, string
            'description':  'The unique key provided to any organization using the WeVoteServer APIs',
        },
    ]
    optional_query_parameter_list = [
    ]

    potential_status_codes_list = [
        {
            'code':         'VALID_VOTER_DEVICE_ID_MISSING',
            'description':  'Cannot proceed. A valid voter_device_id parameter was not included.',
        },
        {
            'code':         'VALID_VOTER_ID_MISSING',
            'description':  'Cannot proceed. A valid voter_id was not found.',
        },
    ]

    try_now_link_variables_dict = {
        # 'campaignx_we_vote_id': 'wv85org1',
    }

    api_response = '{\n' \
                   '  "status": string,\n' \
                   '  "success": boolean,\n' \
                   '  "campaignx_list": list\n' \
                   '   [\n' \
                   '     "campaign_description": string,\n' \
                   '     "campaign_title": string,\n' \
                   '     "campaignx_we_vote_id": string,\n' \
                   '     "in_draft_mode": boolean,\n' \
                   '     "seo_friendly_path": string,\n' \
                   '     "supporters_count": integer,\n' \
                   '     "visible_on_this_site": boolean,\n' \
                   '     "voter_signed_in_with_email": boolean,\n' \
                   '     "voter_we_vote_id": string,\n' \
                   '     "we_vote_hosted_campaign_photo_large_url": string,\n' \
                   '     "we_vote_hosted_campaign_photo_medium_url": string,\n' \
                   '     "we_vote_hosted_campaign_photo_small_url": string,\n' \
                   '     "campaignx_owner_list": list\n' \
                   '     [\n' \
                   '       "organization_name": string,\n' \
                   '       "organization_we_vote_id": string,\n' \
                   '       "we_vote_hosted_profile_image_url_tiny": string,\n' \
                   '       "visible_to_public": boolean,\n' \
                   '     ],\n' \
                   '     "campaignx_politician_list": list\n' \
                   '     [\n' \
                   '       "campaignx_politician_id": integer,\n' \
                   '       "politician_name": string,\n' \
                   '       "politician_we_vote_id": string,\n' \
                   '       "state_code": string,\n' \
                   '       "we_vote_hosted_profile_image_url_large": string,\n' \
                   '       "we_vote_hosted_profile_image_url_medium": string,\n' \
                   '       "we_vote_hosted_profile_image_url_tiny": string,\n' \
                   '     ],\n' \
                   '     "campaignx_politician_list_exists": boolean,\n' \
                   '     "campaignx_politician_starter_list": list\n' \
                   '     [\n' \
                   '       "value": string,\n' \
                   '       "label": string,\n' \
                   '     ],\n' \
                   '     "seo_friendly_path_list": list\n' \
                   '     [],\n' \
                   '   ],\n' \
                   '  "campaign_list_found": boolean,\n' \
                   '  "promoted_campaignx_we_vote_ids": list [],\n' \
                   '  "voter_started_campaignx_we_vote_ids": list [],\n' \
                   '  "voter_supported_campaignx_we_vote_ids": list [],\n' \
                   '}'

    template_values = {
        'api_name': 'campaignListRetrieve',
        'api_slug': 'campaignListRetrieve',
        'api_introduction':
            "",
        'try_now_link': 'apis_v1:campaignListRetrieveView',
        'try_now_link_variables_dict': try_now_link_variables_dict,
        'url_root': url_root,
        'get_or_post': 'GET',
        'required_query_parameter_list': required_query_parameter_list,
        'optional_query_parameter_list': optional_query_parameter_list,
        'api_response': api_response,
        'api_response_notes':
            "",
        'potential_status_codes_list': potential_status_codes_list,
    }
    return template_values
