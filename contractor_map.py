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
    # contractors_df = open(r"data\Contractors\final_contractor_df.csv",'r', encoding="utf8")
    # contractors_df = pd.DataFrame(contractors_df)
    

    url = 'https://github.com/SH290596/test_streamlit_app/blob/main/data/final_contractor_df.csv?raw=true'
    contractors_df = pd.read_csv(url, index_col=0)

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
            "Email",
            "Measure",
            "full_address_google",
            "lat",
            "lon",
            "Air to air Heat Pump check",
            "Air to Water Heat Pump check",
            "Cavity check",
            "Dry-Lining Insulation check",
            "Exhaust Air to Water Heat Pump check",
            "External Insulation check",
            "Ground to Water Heat Pump (Horizontal) check",
            "Ground to Water Heat Pump (Vertical) check",
            "Heating Controls Upgrade only check",
            "High Efficiency Gas Boiler with Heating Controls Upgrade check",
            "High Efficiency Oil Boiler with Heating Controls Upgrade check",
            "Roof Insulation check",
            "Solar Heating check",
            "Water to Water Heat Pump check",
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

    ICON_URL_CHADWICKS = "https://raw.githubusercontent.com/SH290596/test_streamlit_app/main/Chadwicks_C.png"

    icon_data_Chadwicks = {
        "url": ICON_URL_CHADWICKS,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }

    ICON_URL = "https://raw.githubusercontent.com/SH290596/test_streamlit_app/main/icon_green_pin.png"

    icon_data = {
        "url": ICON_URL,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }

    # test_contractor_example["icon_data"] = np.where(
    #     contractors_df["chadwicks_approved"] == True, [icon_data_Chadwicks], [icon_data]
    # )

    test_contractor_example["icon_data"] = [icon_data] * len(test_contractor_example)

    return test_contractor_example


def load_customer_data(lat, lon):
    data = {
        "FullAddress": ["12 Warren Cres, Kevinsfort, Sligo, F91 N6YF"],
        "lat": [lat],
        "lon": [lon],
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
        if any(substring in all_measure_available for substring in selected_upgrades):
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

def filter_df_closet_contractor_offering_measure(df: pd.DataFrame, measure_list: list):
    # -- Logic to decide what contractors to display
    # -- Filter df for closet contractor based on selected method
    test_df = pd.DataFrame(
        columns=[
            "company_name",
            "km_from_you",
            "Mobile",
            "Email",
            "Measure",
            "County",
            "lat",
            "lon",
            "icon_data",
            "full_address_google",
            "Air to air Heat Pump check",
            "Air to Water Heat Pump check",
            "Cavity check",
            "Dry-Lining Insulation check",
            "Exhaust Air to Water Heat Pump check",
            "External Insulation check",
            "Ground to Water Heat Pump (Horizontal) check",
            "Ground to Water Heat Pump (Vertical) check",
            "Heating Controls Upgrade only check",
            "High Efficiency Gas Boiler with Heating Controls Upgrade check",
            "High Efficiency Oil Boiler with Heating Controls Upgrade check",
            "Roof Insulation check",
            "Solar Heating check",
            "Water to Water Heat Pump check",
        ]
    )
    index_list = []

    if not measure_list:
        return test_df
    else:
        for i in measure_list:

            check_df_not_empty = df[df[i + " check"] == True]

            if check_df_not_empty.empty:
                pass
            else:
                filtered_df = df.loc[
                    df[df[i + " check"] == True]
                    .groupby(by=[i + " check"])["km_from_you"]
                    .idxmin()
                ]
                test_df = test_df.append(
                    filtered_df[
                        [
                            "company_name",
                            "km_from_you",
                            "Mobile",
                            "Email",
                            "Measure",
                            "County",
                            "lat",
                            "lon",
                            "icon_data",
                            "full_address_google",
                            "Air to air Heat Pump check",
                            "Air to Water Heat Pump check",
                            "Cavity check",
                            "Dry-Lining Insulation check",
                            "Exhaust Air to Water Heat Pump check",
                            "External Insulation check",
                            "Ground to Water Heat Pump (Horizontal) check",
                            "Ground to Water Heat Pump (Vertical) check",
                            "Heating Controls Upgrade only check",
                            "High Efficiency Gas Boiler with Heating Controls Upgrade check",
                            "High Efficiency Oil Boiler with Heating Controls Upgrade check",
                            "Roof Insulation check",
                            "Solar Heating check",
                            "Water to Water Heat Pump check",
                        ]
                    ],
                    ignore_index=True,
                )

                index_list.append(i)

        # Set Index equal to upgrades
        test_df["Upgrade"] = index_list
        test_df.set_index("Upgrade", inplace=True)
        test_df.index.name = None

        return test_df




def app():

    # -- Remove bar at top of app
    hide_decoration_bar_style = """
    <style>
        header {visibility: hidden;}
    </style>
    """
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

    # Remove whitespace from the top of the page and sidebar
    st.markdown(
        """
        <style>
               .css-18e3th9 {
                    padding-top: 0rem;
                    padding-bottom: 10rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
               .css-1d391kg {
                    padding-top: 3.5rem;
                    padding-right: 1rem;
                    padding-bottom: 3.5rem;
                    padding-left: 1rem;
                }
        </style>
        """,
        unsafe_allow_html=True,
    )

    query_params = st.experimental_get_query_params()

    # -- Default values for querys pulled from url
    lat = float(query_params.get("latitude", [54.2674002])[0])
    lon = float(query_params.get("longitude", [-8.5002254])[0])
    pre_measure_selection = list(query_params.get("measures", ["2"])[0])

    # -- Convert strings in list to numbers
    pre_measure_selection = [int(i) for i in pre_measure_selection]

    # http://localhost:8501/?latitude=53.4495&longitude=-7.5030
    # http://localhost:8501/?latitude=53.4495&longitude=-7.5030&measures=025
    # http://localhost:8501/?latitude=53.279541&longitude=-6.199322&measures=025
    # st.write(query_params)

    df_user = load_customer_data(lat, lon)

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

    # -- Get pre selected measures
    pre_measure_selection = list(measure_list[i] for i in pre_measure_selection)

    st.markdown(
        "<h1 style='text-align: center; color: Black;'>Find A Contractor</h1>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([2, 4, 4])

    with col1:
        st.subheader("Filters")
        # Create a dropdown to filter for upgrade measure
        measure_dropdown = st.multiselect(
            "Select Upgrades", measure_list, default=pre_measure_selection
        )
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
        # chadwicks_approved_fil = st.radio(
        #     label=("Chadwick's Approved Contractor:"), options=("Yes", "No"), index=(0)
        # )

    # -- Filter dataset based off dropdown selection
    df_fil = filter_df_on_distance(df, km_from_home)

    # -- Filter dataset based off chadwicks approved or not
    # df_fil = filter_df_on_chadwicks_approved(df_fil, chadwicks_approved_fil)

    # -- Copy dataset to filter for closet contractor based on upgrade measure
    df_closet_contractor_for_measure = df_fil.copy(deep=False)

    # -- Get Closet contractor based on upgrade measure picked
    df_closet_contractor_for_measure_fil = filter_df_closet_contractor_offering_measure(
        df_closet_contractor_for_measure, measure_dropdown
    )

    # -- Filter dataset based off dropdown selection
    df_fil = filter_df_on_desired_upgrades(df_fil, measure_dropdown)

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

    icon_layer_3 = pdk.Layer(
        type="IconLayer",
        data=df_closet_contractor_for_measure_fil,
        get_icon="icon_data",
        get_size=4,
        size_scale=8,
        get_position=["lon", "lat"],
        pickable=True,
    )

    def checked_or_unchecked(value):
        if value == True:
            return "checked"
        else:
            return "unchecked"

    df_fil["Cavity_checkbox"] = df_fil["Cavity check"].apply(checked_or_unchecked)
    # df_fil["Cavity_checkbox"] = df_fil["Cavity check"]
    # -- Checkbox
    # <input type="checkbox" id= "Cavity" style="vertical-align: middle;" "name="Cavity" {Cavity_checkbox.info}>
    # <label for="Cavity" style="text-align: center;" > Cavity </label>

    tooltip = {
        "html": """<div class="row" style="z-index:99">
                            <div class="column" style="float:left;width: 50%;font-size:15px">
                            <b>Company Name:</b> <br /> {company_name} <br />
                            <b>Phone Number:</b> <br /> {Mobile} <br/> 
                            <b>County:</b> {County} <br/> 
                            <b>KM From You:</b> {km_from_you} Km<br/>
                        </div>
                        <div class="column" style="float:left; text-align: left; width: 50%; padding-left: 10px">
                            <b>Measures Available</b>
                            <div style="font-size:8px">
                            <b>Air to air Heat Pump: {Air to air Heat Pump check} <br />
                            <b>Air to Water Heat Pump: {Air to Water Heat Pump check} <br />
                            <b>Cavity: {Cavity check} <br />
                            <b>Dry-Lining Insulation: {Dry-Lining Insulation check} <br />
                            <b>Exhaust Air to Water Heat Pump: {Exhaust Air to Water Heat Pump check} <br />
                            <b>External Insulation: {External Insulation check} <br />
                            <b>Ground to Water Heat Pump (Horizontal): {Ground to Water Heat Pump (Horizontal) check} <br />
                            <b>Ground to Water Heat Pump (Vertical): {Ground to Water Heat Pump (Vertical) check} <br />
                            <b>Heating Controls Upgrade only: {Heating Controls Upgrade only check} <br />
                            <b>High Efficiency Gas Boiler with Heating Controls Upgrade: {High Efficiency Gas Boiler with Heating Controls Upgrade check} <br />
                            <b>High Efficiency Oil Boiler with Heating Controls Upgrade: {High Efficiency Oil Boiler with Heating Controls Upgrade check} <br />
                            <b>Roof Insulation: {Roof Insulation check} <br />
                            <b>Solar Heating: {Solar Heating check} <br />
                            <b>Water to Water Heat Pump: {Water to Water Heat Pump check} <br />
                            <div/>
                        </div>
                    </div>
                """,
        "style": {
            "backgroundColor": "#198754",
            "color": "white",
            "border-radius": "20px",
            "border-style": "solid",
            "border-color": "#145214",
            "z-index": "99" "!important",
        },
    }

    layers = [icon_layer, icon_layer_2, icon_layer_3]

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
        # -- Closet Contractors For Each Upgrade Measure Table
        st.subheader("Closest Contractor For Upgrade Measure")

        df_closet_contractor_for_measure_fil_final = (
            df_closet_contractor_for_measure_fil[
                [
                    "company_name",
                    "km_from_you",
                    "full_address_google",
                    "Mobile",
                    "Email",
                ]
            ]
        )

        df_closet_contractor_for_measure_fil_final.rename(
            columns={
                "company_name": "Contractor",
                "km_from_you": "Distance From You",
                "full_address_google": "Address",
            },
            inplace=True,
        )

        # -- Style Columns
        mapper = {
            "Distance From You": "{0:.2f} Km",
        }

        st.dataframe(df_closet_contractor_for_measure_fil_final.style.format(mapper))

        # -- Closet Contractors that carry out all upgrades
        st.subheader("Contractors closest To You")

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