# campaign/views_admin.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from .models import CampaignX, CampaignXManager, CampaignXOwner, CampaignXPolitician, CampaignXSupporter
from admin_tools.views import redirect_to_sign_in_page
from config.base import get_environment_variable
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages import get_messages
from django.shortcuts import render
from exception.models import handle_record_found_more_than_one_exception,\
    handle_record_not_deleted_exception, handle_record_not_found_exception
from election.controllers import retrieve_election_id_list_by_year_list, retrieve_upcoming_election_id_list
from election.models import Election, ElectionManager
import json
import operator
from organization.models import OrganizationManager
from politician.models import PoliticianManager
from voter.models import retrieve_voter_authority, voter_has_authority, VoterManager
import wevote_functions.admin
from wevote_functions.functions import convert_to_int, extract_twitter_handle_from_text_string, positive_value_exists, \
    STATE_CODE_MAP

logger = wevote_functions.admin.get_logger(__name__)


@login_required
def campaign_edit_owners_process_view(request):
    """

    :param request:
    :return:
    """
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = {'political_data_manager'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    campaignx_we_vote_id = request.POST.get('campaignx_we_vote_id', None)
    campaignx_owner_organization_we_vote_id = request.POST.get('campaignx_owner_organization_we_vote_id', None)
    campaignx_owner_visible_to_public = \
        positive_value_exists(request.POST.get('campaignx_owner_visible_to_public', False))
    campaignx_owner_feature_this_profile_image = \
        positive_value_exists(request.POST.get('campaignx_owner_feature_this_profile_image', False))
    google_civic_election_id = convert_to_int(request.POST.get('google_civic_election_id', 0))
    state_code = request.POST.get('state_code', '')

    organization_manager = OrganizationManager()

    # Create new CampaignXOwner
    if positive_value_exists(campaignx_owner_organization_we_vote_id):
        do_not_create = False
        link_already_exists = False
        status = ""
        # Does it already exist?
        try:
            CampaignXOwner.objects.get(
                campaignx_we_vote_id=campaignx_we_vote_id,
                organization_we_vote_id=campaignx_owner_organization_we_vote_id)
            link_already_exists = True
        except CampaignXOwner.DoesNotExist:
            link_already_exists = False
        except Exception as e:
            do_not_create = True
            messages.add_message(request, messages.ERROR, 'CampaignXOwner already exists.')
            status += "ADD_CAMPAIGN_OWNER_ALREADY_EXISTS " + str(e) + " "

        if not do_not_create and not link_already_exists:
            organization_results = \
                organization_manager.retrieve_organization_from_we_vote_id(campaignx_owner_organization_we_vote_id)
            if organization_results['organization_found']:
                organization_name = organization_results['organization'].organization_name
                we_vote_hosted_profile_image_url_tiny = \
                    organization_results['organization'].we_vote_hosted_profile_image_url_tiny
            else:
                organization_name = ''
                we_vote_hosted_profile_image_url_tiny = ''
            voter_we_vote_id = ''
            # Now create new link
            try:
                # Create the CampaignXOwner
                CampaignXOwner.objects.create(
                    campaignx_we_vote_id=campaignx_we_vote_id,
                    organization_name=organization_name,
                    organization_we_vote_id=campaignx_owner_organization_we_vote_id,
                    feature_this_profile_image=campaignx_owner_feature_this_profile_image,
                    voter_we_vote_id=voter_we_vote_id,
                    we_vote_hosted_profile_image_url_tiny=we_vote_hosted_profile_image_url_tiny,
                    visible_to_public=campaignx_owner_visible_to_public)

                messages.add_message(request, messages.INFO, 'New CampaignXOwner created.')
            except Exception as e:
                messages.add_message(request, messages.ERROR,
                                     'Could not create CampaignXOwner.'
                                     ' {error} [type: {error_type}]'.format(error=e, error_type=type(e)))

    # ##################################
    # Deleting or editing a CampaignXOwner
    campaignx_manager = CampaignXManager()
    campaignx_owner_list = campaignx_manager.retrieve_campaignx_owner_list(
        campaignx_we_vote_id=campaignx_we_vote_id,
        viewer_is_owner=True
    )
    for campaignx_owner in campaignx_owner_list:
        if positive_value_exists(campaignx_owner.campaignx_we_vote_id):
            delete_variable_name = "delete_campaignx_owner_" + str(campaignx_owner.id)
            delete_campaignx_owner = positive_value_exists(request.POST.get(delete_variable_name, False))
            if positive_value_exists(delete_campaignx_owner):
                campaignx_owner.delete()
                messages.add_message(request, messages.INFO, 'Deleted CampaignXOwner.')
            else:
                owner_changed = False
                visible_to_public_exists_variable_name = \
                    "campaignx_owner_visible_to_public_" + str(campaignx_owner.id) + "_exists"
                campaignx_owner_visible_to_public_exists = \
                    request.POST.get(visible_to_public_exists_variable_name, None)
                visible_to_public_variable_name = "campaignx_owner_visible_to_public_" + str(campaignx_owner.id)
                campaignx_owner_visible_to_public = \
                    positive_value_exists(request.POST.get(visible_to_public_variable_name, False))
                feature_this_profile_image_variable_name = \
                    "campaignx_owner_feature_this_profile_image_" + str(campaignx_owner.id)
                campaignx_owner_feature_this_profile_image = \
                    positive_value_exists(request.POST.get(feature_this_profile_image_variable_name, False))
                if campaignx_owner_visible_to_public_exists is not None:
                    campaignx_owner.feature_this_profile_image = campaignx_owner_feature_this_profile_image
                    campaignx_owner.visible_to_public = campaignx_owner_visible_to_public
                    owner_changed = True

                # Now refresh organization cached data
                organization_results = \
                    organization_manager.retrieve_organization_from_we_vote_id(campaignx_owner.organization_we_vote_id)
                if organization_results['organization_found']:
                    organization_name = organization_results['organization'].organization_name
                    if positive_value_exists(organization_name):
                        campaignx_owner.organization_name = organization_name
                        owner_changed = True
                    we_vote_hosted_profile_image_url_tiny = \
                        organization_results['organization'].we_vote_hosted_profile_image_url_tiny
                    if positive_value_exists(we_vote_hosted_profile_image_url_tiny):
                        campaignx_owner.we_vote_hosted_profile_image_url_tiny = we_vote_hosted_profile_image_url_tiny
                        owner_changed = True
                if owner_changed:
                    campaignx_owner.save()

    return HttpResponseRedirect(reverse('campaign:campaignx_edit_owners', args=(campaignx_we_vote_id,)) +
                                "?google_civic_election_id=" + str(google_civic_election_id) +
                                "&state_code=" + str(state_code))


@login_required
def campaign_edit_owners_view(request, campaignx_id=0, campaignx_we_vote_id=""):
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = {'political_data_manager', 'verified_volunteer'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    google_civic_election_id = request.GET.get('google_civic_election_id', 0)
    state_code = request.GET.get('state_code', '')

    messages_on_stage = get_messages(request)
    campaignx_id = convert_to_int(campaignx_id)
    campaignx_manager = CampaignXManager()
    campaignx = None
    results = campaignx_manager.retrieve_campaignx(campaignx_we_vote_id=campaignx_we_vote_id)

    if results['campaignx_found']:
        campaignx = results['campaignx']

    campaignx_owner_list_modified = []
    campaignx_owner_list = campaignx_manager.retrieve_campaignx_owner_list(
        campaignx_we_vote_id=campaignx_we_vote_id,
        viewer_is_owner=True
    )

    # voter_manager = VoterManager()
    for campaignx_owner in campaignx_owner_list:
        campaignx_owner_list_modified.append(campaignx_owner)

    template_values = {
        'campaignx':                campaignx,
        'campaignx_owner_list':     campaignx_owner_list_modified,
        'google_civic_election_id': google_civic_election_id,
        'messages_on_stage':        messages_on_stage,
        'state_code':               state_code,
    }
    return render(request, 'campaign/campaignx_edit_owners.html', template_values)


@login_required
def campaign_edit_politicians_process_view(request):
    """

    :param request:
    :return:
    """
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = {'political_data_manager'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    campaignx_we_vote_id = request.POST.get('campaignx_we_vote_id', None)
    politician_we_vote_id = request.POST.get('politician_we_vote_id', None)
    google_civic_election_id = convert_to_int(request.POST.get('google_civic_election_id', 0))
    state_code = request.POST.get('state_code', '')

    # Create new CampaignXPolitician
    if positive_value_exists(politician_we_vote_id):
        do_not_create = False
        link_already_exists = False
        status = ""
        # Does it already exist?
        try:
            CampaignXPolitician.objects.get(
                campaignx_we_vote_id=campaignx_we_vote_id,
                politician_we_vote_id=politician_we_vote_id)
            link_already_exists = True
        except CampaignXPolitician.DoesNotExist:
            link_already_exists = False
        except Exception as e:
            do_not_create = True
            messages.add_message(request, messages.ERROR, 'Link already exists.')
            status += "ADD_CAMPAIGN_POLITICIAN_ALREADY_EXISTS " + str(e) + " "

        if not do_not_create and not link_already_exists:
            politician_manager = PoliticianManager()
            politician_results = \
                politician_manager.retrieve_politician_from_we_vote_id(politician_we_vote_id)
            if politician_results['politician_found']:
                politician_name = politician_results['politician'].politician_name
                state_code = politician_results['politician'].state_code
                we_vote_hosted_profile_image_url_large = \
                    politician_results['politician'].we_vote_hosted_profile_image_url_large
                we_vote_hosted_profile_image_url_medium = \
                    politician_results['politician'].we_vote_hosted_profile_image_url_medium
                we_vote_hosted_profile_image_url_tiny = \
                    politician_results['politician'].we_vote_hosted_profile_image_url_tiny
            else:
                politician_name = ''
                we_vote_hosted_profile_image_url_large = ''
                we_vote_hosted_profile_image_url_medium = ''
                we_vote_hosted_profile_image_url_tiny = ''
            voter_we_vote_id = ''
            try:
                # Create the CampaignXPolitician
                CampaignXPolitician.objects.create(
                    campaignx_we_vote_id=campaignx_we_vote_id,
                    politician_name=politician_name,
                    politician_we_vote_id=politician_we_vote_id,
                    state_code=state_code,
                    we_vote_hosted_profile_image_url_large=we_vote_hosted_profile_image_url_large,
                    we_vote_hosted_profile_image_url_medium=we_vote_hosted_profile_image_url_medium,
                    we_vote_hosted_profile_image_url_tiny=we_vote_hosted_profile_image_url_tiny,
                )

                messages.add_message(request, messages.INFO, 'New CampaignXPolitician created.')
            except Exception as e:
                messages.add_message(request, messages.ERROR,
                                     'Could not create CampaignXPolitician.'
                                     ' {error} [type: {error_type}]'.format(error=e, error_type=type(e)))

    # ##################################
    # Deleting or editing a CampaignXPolitician
    campaignx_manager = CampaignXManager()
    campaignx_politician_list = campaignx_manager.retrieve_campaignx_politician_list(
        campaignx_we_vote_id=campaignx_we_vote_id,
    )
    for campaignx_politician in campaignx_politician_list:
        if positive_value_exists(campaignx_politician.campaignx_we_vote_id):
            delete_variable_name = "delete_campaignx_politician_" + str(campaignx_politician.id)
            delete_campaignx_politician = positive_value_exists(request.POST.get(delete_variable_name, False))
            if positive_value_exists(delete_campaignx_politician):
                campaignx_politician.delete()
                messages.add_message(request, messages.INFO, 'Deleted CampaignXPolitician.')
            else:
                pass

    return HttpResponseRedirect(reverse('campaign:campaignx_edit_politicians', args=(campaignx_we_vote_id,)) +
                                "?google_civic_election_id=" + str(google_civic_election_id) +
                                "&state_code=" + str(state_code))


@login_required
def campaign_edit_politicians_view(request, campaignx_id=0, campaignx_we_vote_id=""):
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = {'political_data_manager', 'verified_volunteer'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    google_civic_election_id = request.GET.get('google_civic_election_id', 0)
    state_code = request.GET.get('state_code', '')

    messages_on_stage = get_messages(request)
    campaignx_id = convert_to_int(campaignx_id)
    campaignx_manager = CampaignXManager()
    campaignx = None
    results = campaignx_manager.retrieve_campaignx(campaignx_we_vote_id=campaignx_we_vote_id)

    if results['campaignx_found']:
        campaignx = results['campaignx']

    campaignx_politician_list = campaignx_manager.retrieve_campaignx_politician_list(
        campaignx_we_vote_id=campaignx_we_vote_id,
    )

    template_values = {
        'campaignx':                    campaignx,
        'campaignx_politician_list':    campaignx_politician_list,
        'google_civic_election_id':     google_civic_election_id,
        'messages_on_stage':            messages_on_stage,
        'state_code':                   state_code,
    }
    return render(request, 'campaign/campaignx_edit_politicians.html', template_values)


@login_required
def campaign_edit_process_view(request):
    """

    :param request:
    :return:
    """
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = {'political_data_manager'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    campaignx_id = convert_to_int(request.POST.get('campaignx_id', 0))
    campaignx_we_vote_id = request.POST.get('campaignx_we_vote_id', None)
    campaign_title = request.POST.get('campaign_title', None)
    campaign_description = request.POST.get('campaign_description', None)
    is_blocked_by_we_vote = request.POST.get('is_blocked_by_we_vote', False)
    is_blocked_by_we_vote_reason = request.POST.get('is_blocked_by_we_vote_reason', None)
    is_ok_to_promote_on_we_vote = request.POST.get('is_ok_to_promote_on_we_vote', False)
    politician_starter_list_serialized = request.POST.get('politician_starter_list_serialized', None)
    google_civic_election_id = request.POST.get('google_civic_election_id', 0)
    state_code = request.POST.get('state_code', None)

    # Check to see if this organization is already being used anywhere
    campaignx = None
    campaignx_found = False
    status = ""
    try:
        if positive_value_exists(campaignx_id):
            campaignx = CampaignX.objects.get(id=campaignx_id)
            campaignx_we_vote_id = campaignx.we_vote_id
        else:
            campaignx = CampaignX.objects.get(we_vote_id=campaignx_we_vote_id)
        campaignx_found = True
    except Exception as e:
        messages.add_message(request, messages.ERROR, 'CampaignX can only be edited for existing organization.')
        status += "EDIT_CAMPAIGN_PROCESS_NOT_FOUND " + str(e) + " "

    try:
        if campaignx_found:
            # Update
            if campaign_title is not None:
                campaignx.campaign_title = campaign_title
            if campaign_description is not None:
                campaignx.campaign_description = campaign_description.strip()
            campaignx.is_blocked_by_we_vote = positive_value_exists(is_blocked_by_we_vote)
            if is_blocked_by_we_vote_reason is not None:
                campaignx.is_blocked_by_we_vote_reason = is_blocked_by_we_vote_reason.strip()
            campaignx.is_ok_to_promote_on_we_vote = positive_value_exists(is_ok_to_promote_on_we_vote)
            if politician_starter_list_serialized is not None:
                campaignx.politician_starter_list_serialized = politician_starter_list_serialized.strip()
            campaignx.save()

            messages.add_message(request, messages.INFO, 'CampaignX updated.')
        else:
            # We do not create organizations in this view
            pass
    except Exception as e:
        messages.add_message(request, messages.ERROR, 'Could not save CampaignX.'
                                                      ' {error} [type: {error_type}]'.format(error=e,
                                                                                             error_type=type(e)))

    return HttpResponseRedirect(reverse('campaign:campaignx_edit', args=(campaignx_we_vote_id,)) +
                                "?google_civic_election_id=" + str(google_civic_election_id) +
                                "&state_code=" + str(state_code))


@login_required
def campaign_edit_view(request, campaignx_we_vote_id=""):
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = {'political_data_manager', 'verified_volunteer'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    google_civic_election_id = request.GET.get('google_civic_election_id', 0)

    messages_on_stage = get_messages(request)
    campaignx_manager = CampaignXManager()
    campaignx = None
    results = campaignx_manager.retrieve_campaignx(campaignx_we_vote_id=campaignx_we_vote_id)

    if results['campaignx_found']:
        campaignx = results['campaignx']

    election_manager = ElectionManager()
    upcoming_election_list = []
    results = election_manager.retrieve_upcoming_elections()
    if results['success']:
        upcoming_election_list = results['election_list']

    state_list = STATE_CODE_MAP
    sorted_state_list = sorted(state_list.items())

    template_values = {
        'google_civic_election_id': google_civic_election_id,
        'messages_on_stage':        messages_on_stage,
        'campaignx':                campaignx,
        'state_list':               sorted_state_list,
        'upcoming_election_list':   upcoming_election_list,
    }
    return render(request, 'campaign/campaignx_edit.html', template_values)


@login_required
def campaign_list_view(request):
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = \
        {'partner_organization', 'political_data_manager', 'political_data_viewer', 'verified_volunteer'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    candidate_we_vote_id = request.GET.get('candidate_we_vote_id', '')
    google_civic_election_id = request.GET.get('google_civic_election_id', '')
    limit_to_opinions_in_state_code = request.GET.get('limit_to_opinions_in_state_code', '')
    limit_to_opinions_in_this_year = convert_to_int(request.GET.get('limit_to_opinions_in_this_year', 0))
    campaignx_search = request.GET.get('campaignx_search', '')
    campaignx_type_filter = request.GET.get('campaignx_type_filter', '')
    sort_by = request.GET.get('sort_by', '')
    state_code = request.GET.get('state_code', '')
    show_all = request.GET.get('show_all', False)
    show_more = request.GET.get('show_more', False)  # Show up to 1,000 organizations
    show_issues = request.GET.get('show_issues', '')
    show_organizations_without_email = positive_value_exists(request.GET.get('show_organizations_without_email', False))
    show_campaigns_in_draft = \
        positive_value_exists(request.GET.get('show_campaigns_in_draft', False))

    election_years_available = [2022, 2021, 2020, 2019, 2018, 2017, 2016]

    messages_on_stage = get_messages(request)
    campaignx_list_query = CampaignX.objects.all()

    if positive_value_exists(show_campaigns_in_draft):
        campaignx_list_query = campaignx_list_query.filter(in_draft_mode=True)
    else:
        campaignx_list_query = campaignx_list_query.filter(in_draft_mode=False)

    if positive_value_exists(sort_by):
        # if sort_by == "twitter":
        #     campaignx_list_query = \
        #         campaignx_list_query.order_by('organization_name').order_by('-twitter_followers_count')
        # else:
        campaignx_list_query = campaignx_list_query.order_by('-supporters_count')
    else:
        campaignx_list_query = campaignx_list_query.order_by('-supporters_count')

    # if positive_value_exists(show_organizations_without_email):
    #     campaignx_list_query = campaignx_list_query.filter(
    #         Q(organization_email__isnull=True) |
    #         Q(organization_email__exact='')
    #     )

    if positive_value_exists(campaignx_search):
        search_words = campaignx_search.split()
        for one_word in search_words:
            filters = []
            new_filter = Q(campaign_title__icontains=one_word)
            filters.append(new_filter)

            new_filter = Q(campaign_description__icontains=one_word)
            filters.append(new_filter)

            new_filter = Q(started_by_voter_we_vote_id__icontains=one_word)
            filters.append(new_filter)

            new_filter = Q(we_vote_id__icontains=one_word)
            filters.append(new_filter)

            # Add the first query
            if len(filters):
                final_filters = filters.pop()

                # ...and "OR" the remaining items in the list
                for item in filters:
                    final_filters |= item

                campaignx_list_query = campaignx_list_query.filter(final_filters)

    campaignx_count = campaignx_list_query.count()
    messages.add_message(request, messages.INFO,
                         '{campaignx_count:,} campaigns found.'.format(campaignx_count=campaignx_count))

    # Limit to only showing 200 on screen
    if positive_value_exists(show_more):
        campaignx_list = campaignx_list_query[:1000]
    elif positive_value_exists(show_all):
        campaignx_list = campaignx_list_query
    else:
        campaignx_list = campaignx_list_query[:50]

    # Now loop through these organizations and add owners
    modified_campaignx_list = []
    campaignx_manager = CampaignXManager()
    for campaignx in campaignx_list:
        campaignx.campaignx_owner_list = campaignx_manager.retrieve_campaignx_owner_list(
            campaignx_we_vote_id=campaignx.we_vote_id,
            viewer_is_owner=True)
        modified_campaignx_list.append(campaignx)

    state_list = STATE_CODE_MAP
    sorted_state_list = sorted(state_list.items())

    template_values = {
        'candidate_we_vote_id':     candidate_we_vote_id,
        'election_years_available': election_years_available,
        'google_civic_election_id': google_civic_election_id,
        'limit_to_opinions_in_state_code': limit_to_opinions_in_state_code,
        'limit_to_opinions_in_this_year': limit_to_opinions_in_this_year,
        'messages_on_stage':        messages_on_stage,
        'campaignx_type_filter':    campaignx_type_filter,
        'campaignx_types':          [],
        'campaignx_list':           modified_campaignx_list,
        'campaignx_search':         campaignx_search,
        'show_all':                 show_all,
        'show_issues':              show_issues,
        'show_more':                show_more,
        'show_organizations_without_email': show_organizations_without_email,
        'show_campaigns_in_draft': show_campaigns_in_draft,
        'sort_by':                  sort_by,
        'state_code':               state_code,
        'state_list':               sorted_state_list,
    }
    return render(request, 'campaign/campaignx_list.html', template_values)


@login_required
def campaign_summary_view(request, campaignx_we_vote_id=""):
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = {'political_data_manager', 'verified_volunteer'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    google_civic_election_id = request.GET.get('google_civic_election_id', 0)
    state_code = request.GET.get('state_code', '')

    messages_on_stage = get_messages(request)
    campaignx_manager = CampaignXManager()
    campaignx = None

    results = campaignx_manager.retrieve_campaignx(campaignx_we_vote_id=campaignx_we_vote_id)

    if results['campaignx_found']:
        campaignx = results['campaignx']

    campaignx_owner_list_modified = []
    campaignx_owner_list = campaignx_manager.retrieve_campaignx_owner_list(
        campaignx_we_vote_id=campaignx_we_vote_id,
        viewer_is_owner=True
    )

    for campaignx_owner in campaignx_owner_list:
        campaignx_owner_list_modified.append(campaignx_owner)

    campaignx_politician_list_modified = []
    campaignx_politician_list = campaignx_manager.retrieve_campaignx_politician_list(
        campaignx_we_vote_id=campaignx_we_vote_id,
    )

    for campaignx_politician in campaignx_politician_list:
        campaignx_politician_list_modified.append(campaignx_politician)

    supporters_query = CampaignXSupporter.objects.all()
    supporters_query = supporters_query.filter(campaignx_we_vote_id__iexact=campaignx_we_vote_id)
    supporters_query = supporters_query.exclude(
        Q(supporter_endorsement__isnull=True) |
        Q(supporter_endorsement__exact='')
    )
    campaignx_supporter_list = list(supporters_query[:4])

    campaignx_supporters_count = campaignx_manager.fetch_campaignx_supporter_count(campaignx_we_vote_id)

    template_values = {
        'campaignx':                campaignx,
        'campaignx_owner_list':     campaignx_owner_list_modified,
        'campaignx_politician_list': campaignx_politician_list_modified,
        'campaignx_supporters_count': campaignx_supporters_count,
        'campaignx_supporter_list': campaignx_supporter_list,
        'google_civic_election_id': google_civic_election_id,
        'messages_on_stage':        messages_on_stage,
        'state_code':               state_code,
    }
    return render(request, 'campaign/campaignx_summary.html', template_values)


@login_required
def campaign_supporters_list_view(request, campaignx_we_vote_id=""):
    # admin, analytics_admin, partner_organization, political_data_manager, political_data_viewer, verified_volunteer
    authority_required = \
        {'partner_organization', 'political_data_manager', 'political_data_viewer', 'verified_volunteer'}
    if not voter_has_authority(request, authority_required):
        return redirect_to_sign_in_page(request, authority_required)

    candidate_we_vote_id = request.GET.get('candidate_we_vote_id', '')
    google_civic_election_id = request.GET.get('google_civic_election_id', '')
    limit_to_opinions_in_state_code = request.GET.get('limit_to_opinions_in_state_code', '')
    limit_to_opinions_in_this_year = convert_to_int(request.GET.get('limit_to_opinions_in_this_year', 0))
    campaignx_search = request.GET.get('campaignx_search', '')
    campaignx_type_filter = request.GET.get('campaignx_type_filter', '')
    sort_by = request.GET.get('sort_by', '')
    state_code = request.GET.get('state_code', '')
    show_all = request.GET.get('show_all', False)
    show_more = request.GET.get('show_more', False)  # Show up to 1,000 organizations
    show_issues = request.GET.get('show_issues', '')
    show_supporters_without_endorsements = \
        positive_value_exists(request.GET.get('show_supporters_without_endorsements', False))
    show_supporters_not_visible_to_public = \
        positive_value_exists(request.GET.get('show_supporters_not_visible_to_public', False))

    election_years_available = [2022, 2021, 2020, 2019, 2018, 2017, 2016]

    messages_on_stage = get_messages(request)

    campaignx = CampaignX.objects.get(we_vote_id__iexact=campaignx_we_vote_id)
    campaignx_title = campaignx.campaign_title

    supporters_query = CampaignXSupporter.objects.all()
    supporters_query = supporters_query.filter(campaignx_we_vote_id__iexact=campaignx_we_vote_id)

    if positive_value_exists(show_supporters_without_endorsements):
        pass
    else:
        supporters_query = supporters_query.exclude(
            Q(supporter_endorsement__isnull=True) |
            Q(supporter_endorsement__exact='')
        )

    supporters_query = supporters_query.order_by('-date_supported')

    if positive_value_exists(show_supporters_not_visible_to_public):
        pass
    else:
        # Default to only show visible_to_public
        supporters_query = supporters_query.filter(visible_to_public=True)

    # if positive_value_exists(state_code):
    #     supporters_query = supporters_query.filter(state_served_code__iexact=state_code)
    #
    # if positive_value_exists(campaignx_type_filter):
    #     if campaignx_type_filter == UNKNOWN:
    #         # Make sure to also show organizations that are not specified
    #         supporters_query = supporters_query.filter(
    #             Q(organization_type__iexact=campaignx_type_filter) |
    #             Q(organization_type__isnull=True) |
    #             Q(organization_type__exact='')
    #         )
    #     else:
    #         supporters_query = supporters_query.filter(organization_type__iexact=campaignx_type_filter)
    # else:
    #     # By default, don't show individuals
    #     supporters_query = supporters_query.exclude(organization_type__iexact=INDIVIDUAL)

    if positive_value_exists(campaignx_search):
        search_words = campaignx_search.split()
        for one_word in search_words:
            filters = []
            new_filter = Q(supporter_name__icontains=one_word)
            filters.append(new_filter)

            new_filter = Q(supporter_endorsement__icontains=one_word)
            filters.append(new_filter)

            new_filter = Q(voter_we_vote_id__icontains=one_word)
            filters.append(new_filter)

            new_filter = Q(organization_we_vote_id__icontains=one_word)
            filters.append(new_filter)

            # Add the first query
            if len(filters):
                final_filters = filters.pop()

                # ...and "OR" the remaining items in the list
                for item in filters:
                    final_filters |= item

                supporters_query = supporters_query.filter(final_filters)

    supporters_count = supporters_query.count()
    messages.add_message(request, messages.INFO,
                         'Showing {supporters_count:,} campaign supporters.'.format(supporters_count=supporters_count))

    # Limit to only showing 200 on screen
    if positive_value_exists(show_more):
        supporters_list = supporters_query[:1000]
    elif positive_value_exists(show_all):
        supporters_list = supporters_query
    else:
        supporters_list = supporters_query[:200]

    state_list = STATE_CODE_MAP
    sorted_state_list = sorted(state_list.items())

    template_values = {
        'campaignx_we_vote_id':     campaignx_we_vote_id,
        'campaignx_search':         campaignx_search,
        'campaignx_title':          campaignx_title,
        'election_years_available': election_years_available,
        'google_civic_election_id': google_civic_election_id,
        'limit_to_opinions_in_state_code': limit_to_opinions_in_state_code,
        'limit_to_opinions_in_this_year': limit_to_opinions_in_this_year,
        'messages_on_stage':        messages_on_stage,
        'campaignx_type_filter':    campaignx_type_filter,
        'campaignx_types':          [],
        'supporters_list':          supporters_list,
        'show_all':                 show_all,
        'show_issues':              show_issues,
        'show_more':                show_more,
        'show_supporters_not_visible_to_public': show_supporters_not_visible_to_public,
        'show_supporters_without_endorsements': show_supporters_without_endorsements,
        'sort_by':                  sort_by,
        'state_code':               state_code,
        'state_list':               sorted_state_list,
    }
    return render(request, 'campaign/campaignx_supporters_list.html', template_values)
