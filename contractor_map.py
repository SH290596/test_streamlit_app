## Import packages
import numpy as np
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import streamlit as st
import json
import geopy.distance
import random


st.set_page_config(layout="wide")


@st.cache(allow_output_mutation=True)
def load_data(user_cord):
    contractors_df = pd.read_csv(r"data\Contractors\final_contractor_df.csv")

    # -- Add zero in front of all mobile number
    contractors_df["Mobile"] = contractors_df["Mobile"].apply(
        lambda x: str(x).zfill(10)
    )

    # contractors_df = contractors_df[contractors_df["eircode"].notnull() == True]
    contractors_df = contractors_df[contractors_df["useful_address"] == True]

    contractors_df = contractors_df[
        [
            "Company/Trading Name",
            "County",
            "Mobile",
            "Measure",
            "full_address_google",
            "lat",
            "lon",
        ]
    ]

    # -- Set random Chadwicks approved contractors
    contractors_df["chadwicks_approved"] = random.choices(
        [True, False], weights=[4, 6], k=len(contractors_df)
    )

    # -- Get contractor location in tuple form
    contractors_df["contactor_location"] = contractors_df[["lat", "lon"]].apply(
        tuple, axis=1
    )
    # -- Function calculate the distance in KM from user
    def get_km_from_user(contractor_loaction, user_location):
        return round(geopy.distance.geodesic(user_location, contractor_loaction).km, 2)

    # -- Run function to calcuate the distance in km from user
    contractors_df["km_from_you"] = contractors_df["contactor_location"].apply(
        get_km_from_user, user_location=user_cord
    )

    test_contractor_example = contractors_df.rename(
        columns={"Company/Trading Name": "company_name"}
    )

    ICON_URL = "https://img.icons8.com/fluency/344/map-pin.png"

    icon_data = {
        "url": ICON_URL,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }

    test_contractor_example["icon_data"] = [icon_data] * len(test_contractor_example)

    return test_contractor_example


def load_customer_data():
    data = {
        "FullAddress": ["12 Warren Cres, Kevinsfort, Sligo, F91 N6YF"],
        "lat": [54.2674002],
        "lon": [-8.5002254],
    }
    addresses = pd.DataFrame(data)

    ICON_URL = "https://img.icons8.com/ios-filled/344/map-pin.png"

    icon_data = {
        "url": ICON_URL,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }

    addresses["icon_data"] = [icon_data]

    return addresses


def filter_df_on_desired_upgrades(df: pd.DataFrame, measure_list: list):
    # -- Function to check if selected upgradeare in the measure string
    def check_measure_present(all_measure_available: str, selected_upgrades: str):
        if all(substring in all_measure_available for substring in selected_upgrades):
            return True
        else:
            return False

    # -- Logic to decide what contractors to display
    if not measure_list:
        return df
    else:
        df["display_contractor"] = df["Measure"].apply(
            check_measure_present, selected_upgrades=measure_list
        )
        df = df[df["display_contractor"] == True]
        return df


def filter_df_on_distance(df: pd.DataFrame, km_from_home_critera: str):
    # -- Logic to decide what contractors to display
    # -- Extract number from string
    distance_in_km = [int(i) for i in km_from_home_critera.split() if i.isdigit()]
    distance_in_km = distance_in_km[0]
    # -- Filter df for all contractors whose km is less than selctect
    df = df[df["km_from_you"] <= distance_in_km]

    return df


def filter_df_on_chadwicks_approved(df: pd.DataFrame, chadwicks_approved_fil: str):
    # -- Logic to decide what contractors to display
    # -- Filter df for all contractors who is chadwick's approved
    if chadwicks_approved_fil == "Yes":
        df = df[df["chadwicks_approved"] == True]
        return df
    else:
        return df


def app():

    df_user = load_customer_data()
    user_cord = (df_user.lat[0], df_user.lon[0])
    df = load_data(user_cord)

    measure_list = [
        "Air to air Heat Pump",
        "Air to Water Heat Pump",
        "Cavity",
        "Dry-Lining Insulation",
        "Exhaust Air to Water Heat Pump",
        "External Insulation",
        "Ground to Water Heat Pump (Horizontal)",
        "Ground to Water Heat Pump (Vertical)",
        "Heating Controls Upgrade only",
        "High Efficiency Gas Boiler with Heating Controls Upgrade",
        "High Efficiency Oil Boiler with Heating Controls Upgrade",
        "Roof Insulation",
        "Solar Heating",
        "Water to Water Heat Pump",
    ]

    st.markdown(
        "<h1 style='text-align: center; color: Black;'>Find A Contractor</h1>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([2, 4, 4])

    with col1:
        st.subheader("Filters")
        # Create a dropdown to filter for upgrade measure
        measure_dropdown = st.multiselect("Select Upgrades", measure_list)
        # Create Radio Buttons for distance from home
        km_from_home = st.radio(
            label="Distance from Home",
            options=["5 km", "10 km", "20 km", "50 km", "100 km", "200 km", "500 km"],
            index=6,
        )
        st.write(
            "<style>div.row-widget.stRadio > div{flex-direction:row;}</style>",
            unsafe_allow_html=True,
        )
        # Create filter for chadwicks approved or not
        chadwicks_approved_fil = st.select_slider(
            "Chadwick's Approved Contractor:", ["No", "Yes"], value="Yes"
        )

    # -- Filter dataset based off dropdown selection
    df_fil = filter_df_on_desired_upgrades(df, measure_dropdown)

    # -- Filter dataset based off dropdown selection
    df_fil = filter_df_on_distance(df_fil, km_from_home)

    # -- Filter dataset based off chadwicks approved or not
    df_fil = filter_df_on_chadwicks_approved(df_fil, chadwicks_approved_fil)

    initial_view_state = pdk.ViewState(
        latitude=53.574449758314195,
        longitude=-6.106089702889869,
        zoom=5,
        max_zoom=16,
        pitch=0,
        bearing=0,
        height=600,
        width=None,
    )

    icon_layer = pdk.Layer(
        type="IconLayer",
        data=df_fil,
        get_icon="icon_data",
        get_size=4,
        size_scale=8,
        get_position=["lon", "lat"],
        pickable=True,
    )

    icon_layer_2 = pdk.Layer(
        type="IconLayer",
        data=df_user,
        get_icon="icon_data",
        get_size=4,
        size_scale=10,
        get_position=["lon", "lat"],
        pickable=False,
    )

    tooltip = {
        "html": """<b>Company Name:</b> {company_name} <br />
                    <b>Phone Number:</b> {Mobile} <br/> 
                    <b>County:</b> {County} <br/> 
                    <b>KM From You:</b> {km_from_you} Km<br/>
        """
    }

    layers = [icon_layer, icon_layer_2]

    r = pdk.Deck(
        layers=layers,
        initial_view_state=initial_view_state,
        map_style="light",
        tooltip=tooltip,
    )

    with col2:
        st.subheader("Interactive Map")
        st.pydeck_chart(r)

    with col3:
        st.subheader("Contractors Closet To You")

        df_closet_contractors = df_fil[
            ["company_name", "km_from_you", "full_address_google", "Mobile", "Measure"]
        ].sort_values(by=["km_from_you"], ascending=True)

        df_closet_contractors.rename(
            columns={
                "company_name": "Contractor",
                "km_from_you": "Distance From You",
                "full_address_google": "Address",
                "Measure": "Services Offered",
            },
            inplace=True,
        )

        df_closet_contractors.set_index("Contractor", inplace=True)

        # -- Style Columns
        mapper = {
            "Distance From You": "{0:.2f} Km",
        }

        st.dataframe(df_closet_contractors.head(10).style.format(mapper))


app()
