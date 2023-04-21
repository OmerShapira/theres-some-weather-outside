# __all__ = ["get_owm_icon_url"]
# WMO Weather interpretation codes (WW)
#  https://open-meteo.com/en/docs
meteo = """
Code	Description
0	Clear sky
1, 2, 3	Mainly clear, partly cloudy, and overcast
45, 48	Fog and depositing rime fog
51, 53, 55	Drizzle: Light, moderate, and dense intensity
56, 57	Freezing Drizzle: Light and dense intensity
61, 63, 65	Rain: Slight, moderate and heavy intensity
66, 67	Freezing Rain: Light and heavy intensity
71, 73, 75	Snow fall: Slight, moderate, and heavy intensity
77	Snow grains
80, 81, 82	Rain showers: Slight, moderate, and violent
85, 86	Snow showers slight and heavy
95 *	Thunderstorm: Slight or moderate
96, 99 *	Thunderstorm with slight and heavy hail
"""

meteo2owm = {
    0:"01",
    1:"02",
    2:"03",
    3:"04",
    45:"50",
    48:"50",
    51:"09",
    53:"09",
    55:"09",
    56:"13",
    57:"13",
    61:"10",
    63:"10",
    65:"10",
    66:"13",
    67:"13",
    71:"13",
    73:"13",
    75:"13",
    77:"13",
    80:"09",
    81:"09",
    82:"09",
    85:"13",
    86:"13",
    95:"11",
    96:"11",
    99:"11"
}

def get_owm_icon_url(openmeteo_code:int, is_night:bool=False, magnify:int=2) -> str: 
    meteo2owm.get(openmeteo_code, "01")
    icon=f"{openmeteo_code}{'n' if is_night else 'd'}@{magnify}x"
    OWM_API = f"https://openweathermap.org/img/wn/{icon}.png"
    return OWM_API

owm = """
200,Thunderstorm,thunderstorm with light rain,11d
201,Thunderstorm,thunderstorm with rain,11d
202,Thunderstorm,thunderstorm with heavy rain,11d
210,Thunderstorm,light thunderstorm,11d
211,Thunderstorm,thunderstorm,11d
212,Thunderstorm,heavy thunderstorm,11d
221,Thunderstorm,ragged thunderstorm,11d
230,Thunderstorm,thunderstorm with light drizzle,11d
231,Thunderstorm,thunderstorm with drizzle,11d
232,Thunderstorm,thunderstorm with heavy drizzle,11d
300,Drizzle,light intensity drizzle,09d
301,Drizzle,drizzle,09d
302,Drizzle,heavy intensity drizzle,09d
310,Drizzle,light intensity drizzle rain,09d
311,Drizzle,drizzle rain,09d
312,Drizzle,heavy intensity drizzle rain,09d
313,Drizzle,shower rain and drizzle,09d
314,Drizzle,heavy shower rain and drizzle,09d
321,Drizzle,shower drizzle,09d
500,Rain,light rain,10d
501,Rain,moderate rain,10d
502,Rain,heavy intensity rain,10d
503,Rain,very heavy rain,10d
504,Rain,extreme rain,10d
511,Rain,freezing rain,13d
520,Rain,light intensity shower rain,09d
521,Rain,shower rain,09d
522,Rain,heavy intensity shower rain,09d
531,Rain,ragged shower rain,09d
600,Snow,light snow,13d
601,Snow,snow,13d
602,Snow,heavy snow,13d
611,Snow,sleet,13d
612,Snow,light shower sleet,13d
613,Snow,shower sleet,13d
615,Snow,light rain and snow,13d
616,Snow,rain and snow,13d
620,Snow,light shower snow,13d
621,Snow,shower snow,13d
622,Snow,heavy shower snow,13d
701,Mist,mist,50d
711,Smoke,smoke,50d
721,Haze,haze,50d
731,Dust,sand/dust whirls,50d
741,Fog,fog,50d
751,Sand,sand,50d
761,Dust,dust,50d
762,Ash,volcanic ash,50d
771,Squall,squalls,50d
781,Tornado,tornado,50d
800,Clear,clear sky,01d
801,Clouds,few clouds: 11-25%,02d
802	Clouds,scattered clouds: 25-50%,03d
803	Clouds,broken clouds: 51-84%,04d
804	Clouds,overcast clouds: 85-100%,04d
"""