import json
from datetime import datetime, date, timedelta
import logging
import requests


hs_api_key = '42ea51c6-d18b-4068-95c4-824e1f8c23bb'


def authorization():
    url = "https://www2.ispe.org/Asi.Scheduler_IMIS/token"  # production iMIS

    # production credentials
    payload = {"Username": "webservice",
               "Password": "t3chtr@nsfer99",
               "Grant_type": "password"
               }

    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
    }

    response = requests.post(url, data=payload, headers=headers)
    # print("Auth resp: ", response)
    data = response.json()

    # print(data['access_token'])
    access_token = data['access_token']
    # print(access_token)
    return access_token


def get_promo_code_iqa(token, offset):
    yesterday_datetime = datetime.today() - timedelta(days=1)
    yest_datetime_frmt = yesterday_datetime.strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S.000000')
    url = f"https://www2.ispe.org/Asi.Scheduler_IMIS/api/iqa?QueryName=$/ISPEIQA/Queries/HubSpot/HS_PromoCodes&offset={offset}&limit=100"

    headers = {
        'Content-Type': "application/json",
        'authorization': 'Bearer {}'.format(token)
    }

    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)
    return data


# get_promo_code_iqa(authorization(),0)


# function returns iMIS contact email, given iMIS contact ID
def get_imis_contact(imis_id):
    url = f'https://www2.ispe.org/Asi.Scheduler_IMIS/api/Party/{imis_id}'

    headers = {
        'Content-Type': "application/json",
        'authorization': f'Bearer {authorization()}'
    }
    req = requests.get(url, headers=headers)
    res = req.json()

    return res


# function returns iMIS contact email, given iMIS contact ID
def get_imis_contact_email(imis_id):
    url = f'https://www2.ispe.org/Asi.Scheduler_IMIS/api/Party/{imis_id}'

    headers = {
        'Content-Type': "application/json",
        'authorization': f'Bearer {authorization()}'
    }
    req = requests.get(url, headers=headers)
    res = req.json()
    try:
        email = res['Emails']['$values'][0]['Address']

        return email
    except:
        email = ''

        return email


# function returns HubSpot contact ID, given HubSpot contact email
def get_hs_contact_id(email):
    url = f'https://api.hubapi.com/contacts/v1/contact/email/{email}/profile?hapikey={hs_api_key}'
    headers = {"Content-Type": "application/json"}

    req = requests.get(url, headers=headers)
    res = req.json()

    try:
        contact_id = res['vid']

        return contact_id
    except Exception as e:
        pass


# function returns associated HubSpot Deal IDs, given HubSpot contact ID
def get_associated_hs_deals(cid):
    assoc_deal_ids = []

    has_more = True
    offset = 0
    while has_more:
        assoc_url = f'https://api.hubapi.com/crm-associations/v1/associations/{cid}/HUBSPOT_DEFINED/4?hapikey={hs_api_key}&limit=100'
        headers = {"Content-Type": "application/json"}

        req = requests.get(assoc_url, headers=headers)
        res = req.json()

        for assoc_id in res['results']:
            assoc_deal_ids.append(assoc_id)
        has_more = res['hasMore']

    return assoc_deal_ids


# function creates HubSpot contact if new or updates existing contact, given email (email returned, given iMIS ID)
def create_or_update_hs_contact(imis_id):
    '''
    Paginates through the API using the IQA UserSearch
    Variables:
    token = Gathers Authorization token from the iMIS system running the authorization function
    offset = offset number for the contacts on the next page
    user_data = dictionary of each user that will get pushed in to HubSpot.
    '''

    today = date.today()

    # logging.basicConfig(filename=f'/home/oboagency/hubspot/logging/createUpdateContact{today}.log', level=logging.DEBUG,
    #                     format='%(asctime)s:%(levelname)s:%(message)s')

    user_data = get_imis_contact(imis_id)  # gets a new request for the new offset range

    cid = user_data['Id']
    try:
        status = user_data['Status']['PartyStatusId']
    except:
        status = ''
    if status == 'A':
        status = 'A – Active'
    elif status == 'S':
        status = 'S – Suspended'
    elif status == 'D':
        status = 'D – Deletion'
    elif status == 'I':
        status = 'I – Inactive'
    for value in user_data['AdditionalAttributes']['$values']:
        if value['Name'] == 'CustomerTypeCode':
            try:
                member_type = value['Value']
            except:
                member_type = ''
    for value in user_data['AdditionalAttributes']['$values']:
        if value['Name'] == 'JoinDate':
            try:
                join_date = value['Value']
            except:
                join_date = ''
    if join_date != '':
        try:
            join_date = int(datetime.strptime(join_date, '%Y-%m-%dT%H:%M:%S').timestamp() * 1000)
        except:
            join_date = ''
    try:
        prefix = user_data['PersonName']['NamePrefix']
    except:
        prefix = ''
    try:
        first_name = user_data['PersonName']['FirstName']
    except:
        first_name = ''
    try:
        last_name = user_data['PersonName']['LastName']
    except:
        last_name = ''
    try:
        title = user_data['PrimaryOrganization']['Title']
    except:
        title = ''
    if title == 'A':
        title = 'A - CEO/President/Owner/General Mgr'
    elif title == 'B':
        title = 'B - Vice President/Chief Officer'
    elif title == 'C':
        title = 'C - Director/Division Mgr/Senior Mgr'
    elif title == 'D':
        title = 'D - Manager/Section Head/Supervisor'
    elif title == 'E':
        title = 'E - Team Lead/Operator/Technician/Staff'
    elif title == 'F':
        title = 'F - Dean/Professor/Educator'
    elif title == 'G':
        title = 'G - Student/Post-Doctoral Fellow'
    elif title == 'H':
        title = 'H - Retired'
    elif title == 'ZZ':
        title = 'ZZ - Other (Please Specify)'
    try:
        company = user_data['PrimaryOrganization']['Name']
    except:
        company = ''

    for val in user_data['Addresses']['$values']:
        try:
            address = val['Address']['AddressLines']['$values'][0]
        except:
            address = ''
        try:
            city = val['Address']['CityName']
        except:
            city = ''
        try:
            state = val['Address']['CountrySubEntityCode']
        except:
            state = ''
        try:
            zipcode = val['Address']['PostalCode']
        except:
            zipcode = ''
        try:
            country = val['Address']['CountryName']
        except:
            country = ''
    try:
        for e in user_data['Emails']['$values']:
            if e['EmailType'] == '_Primary':
                email = e['Address']
    except:
        email = ''
        pass  # if no email, cannot create/update HubSpot contact; pass

    try:
        date_added = user_data['UpdateInformation']['CreatedOn'].split(".")[0]
    except:
        date_added = ''
    if date_added != '':
        date_added = int(datetime.strptime(date_added, '%Y-%m-%dT%H:%M:%S').timestamp() * 1000)
    try:
        last_update = user_data['UpdateInformation']['UpdatedOn'].split(".")[0]
    except:
        last_update = ''
    if last_update != '':
        last_update = int(datetime.strptime(last_update, '%Y-%m-%dT%H:%M:%S').timestamp() * 1000)

    # payload to update HubSpot contact fields
    hs_payload = {
        "properties": [
            {
                "property": "imis_id",
                "value": cid
            },
            {
                "property": "imis_status",
                "value": status
            },
            {
                "property": "member_type",
                "value": member_type
            },
            {
                "property": "member_standing",
                "value": status
            },
            {
                "property": "firstname",
                "value": first_name
            },
            {
                "property": "lastname",
                "value": last_name
            },
            {
                "property": "jobtitle",
                "value": title
            },
            {
                "property": "company",
                "value": company
            },
            {
                "property": "address",
                "value": address
            },
            {
                "property": "city",
                "value": city
            },
            {
                "property": "state",
                "value": state
            },
            {
                "property": "zip",
                "value": zipcode
            },
            {
                "property": "country",
                "value": country
            },
            {
                "property": "email",
                "value": email
            },
            {
                "property": "imis_date_added",
                "value": date_added
            },
            {
                "property": "imis_last_updated",
                "value": last_update
            },
            {
                "property": "salutation",
                "value": prefix
            },
            {
                "property": "imis_join_added",
                "value": join_date
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    create_update_url = f'https://api.hubapi.com/contacts/v1/contact/createOrUpdate/email/{email}/?hapikey={hs_api_key}'
    req = requests.post(create_update_url, data=json.dumps(hs_payload), headers=headers)
    res = req.json()
    print('Craete/Update Contact', res)

    # logging.debug(res)


def create_hs_deal(imis_id, promo_code, promo_code_used_for, date_promo_code_used, sole_num):
    today = date.today()
    # open logging file
    # logging.basicConfig(filename=f'/home/oboagency/hubspot/logging/abandonedRegistration{today}.log', level=logging.DEBUG,
    #                     format='%(asctime)s:%(levelname)s:%(message)s')

    url = f'https://api.hubapi.com/deals/v1/deal?hapikey={hs_api_key}'
    headers = {"Content-Type": "application/json"}
    payload = {
        "associations": {
            "associatedVids": [get_hs_contact_id(get_imis_contact_email(imis_id))]
        },
        "properties": [
            {
                "name": "dealname",
                "value": f"Promo_Code_{promo_code}"
            },
            {
                "name": "dealstage",
                "value": "919189"
            },
            {
                "name": "pipeline",
                "value": "919188"
            },
            {
                "name": "promo_code",
                "value": promo_code
            },
            {
                "name": "promo_code_used_for",
                "value": promo_code_used_for
            },
            {
                "name": "date_promo_code_used",
                "value": date_promo_code_used
            },
            {
                "name": "imis_id",
                "value": imis_id
            },
            {
                "name": "promo_code_sole_num",
                "value": sole_num
            },
        ]
    }

    req = requests.post(url, headers=headers, data=json.dumps(payload))
    print('Create Deal Req', req)
    res = req.json()
    print('Create Deal Response',res)

    # logging.debug(res)


def main_function():
    promo_code_data = {}  # initializes a dictionary that will store the contact data

    has_next = True
    offset = 0
    while has_next:
        data = get_promo_code_iqa(authorization(), offset)  # gets a new request for the new offset range
        # for page in data:
        for i in data['Items']['$values']:
            for value in i['Properties']['$values']:  # for each contact in data
                if value['Name'] == 'ResultRow':  # removes the ResultRow value since that is not needed in HubSpot
                    continue  # continues to the next contact field
                else:
                    try:
                        # adds the contact field and value to cart_data dictionary
                        promo_code_data[value['Name']] = value['Value']
                    except:
                        promo_code_data[value['Name']] = ''
            # print(promo_code_data)  # prints promo_code_data dictionary for testing

            # define fields and convert date fields to unix milliseconds
            st_id = promo_code_data['Id']
            sole_num = promo_code_data['Sole_Num']
            promo_code = promo_code_data['Promo_Code']
            promo_code_used_for = promo_code_data['Where_Used']
            date_promo_code_used = promo_code_data['Date']

            # cur_date = datetime.today()
            # print(cur_date - datetime.strptime(order_date, "%Y-%m-%dT%H:%M:%S"))
            # if cur_date - datetime.strptime(order_date, "%Y-%m-%dT%H:%M:%S") <= timedelta(days=2*365):
            #     print('<2 yrs')
                # for each iMIS contact ID, return contact email
            imis_email = get_imis_contact_email(st_id)
            print('iMIS Email', imis_email)

            try:
                # for each returned contact email, create or update HubSpot contact
                create_or_update_hs_contact(st_id)
                print('create/update success')
            except:
                promo_code_data = {}  # clears promo_code_data dictionary for next item in request
                continue
            # try/except block to handle if iMIS email is not valid format
            try:
                # for each returned iMIS email, get corresponding HubSpot contact associated deals
                assoc_deals = get_associated_hs_deals(get_hs_contact_id(imis_email))
                print('Assoc Deals', assoc_deals)
            except:
                promo_code_data = {}  # clears promo_code_data dictionary for next item in request
                continue

            assoc_deals_promo_code_sole_nums = []

            if not assoc_deals:
                create_hs_deal(
                    imis_id=st_id, promo_code=promo_code, promo_code_used_for=promo_code_used_for,
                    date_promo_code_used=date_promo_code_used, sole_num=sole_num
                )

                promo_code_data = {}  # clears promo_code_data dictionary for next item in request
                continue

            # loop thru associated HS deal IDs to return deal cart ID
            for deal_id in assoc_deals:
                deal_url = f'https://api.hubapi.com/deals/v1/deal/{deal_id}?hapikey={hs_api_key}&property=promo_code_sole_num'
                headers = {"Content-Type": "application/json"}

                req = requests.get(deal_url, headers=headers)
                res = req.json()

                try:
                    deal_sole_num = res['properties']['promo_code_sole_num']['value']
                except:
                    deal_sole_num = ''

                assoc_deals_promo_code_sole_nums.append(deal_sole_num)

            # if HS Deal cart ID equal to iMIS cart ID, deal already created; continue
            if sole_num in assoc_deals_promo_code_sole_nums:

                promo_code_data = {}  # clears promo_code_data dictionary for next item in request
                continue
            # else, deal not yet created; create deal
            else:
                create_hs_deal(
                    imis_id=st_id, promo_code=promo_code, promo_code_used_for=promo_code_used_for,
                    data_promo_code_used=date_promo_code_used, sole_num=sole_num
                )

        else:
            promo_code_data = {}  # clears promo_code_data dictionary for next item in request
            continue

        promo_code_data = {}  # clears the promo_code_data dictionary for the next contact in the request

        has_next = data['HasNext']
        offset = data['NextOffset']


main_function()
