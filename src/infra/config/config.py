COMPETITORS_NAUSY = {
    "sailamor": {
        "competitor_name": "sailamor",
        "yacht_ids": {
            "Athena 5": "52110487",
            "Athena 2": "52110484",
            "Athena 4": "52110486",
            "Moana": "52071436",
            "Moana 2": "52110483"
        },
        "search_text": "Sailamor",
        "click_text": "Sailamor"
    },
    "rudder": {
        "competitor_name": "rudder",
        "yacht_ids": {
            "mithra": "34431226",
            "mizu": "34669522"
        },
        "search_text": "rudder",
        "click_text": "rudder&moor"
    },
    "egg_yachting": {
        "competitor_name": "egg_yachting",
        "yacht_ids": {
            "moonrise": "12897626"
        },
        "search_text": "e.g.g.",
        "click_text": "E.G.G. Yachting"
    },
    "asmira_marine": {
        "competitor_name": "asmira_marine",
        "yacht_ids": {
            "pamina": "13566528"
        },
        "search_text": "asmira",
        "click_text": "Asmira Marine Yacht Charter"
    },
    "cordelia": {
        "competitor_name": "cordelia_yachting",
        "yacht_ids": {
            "First Step": "25462650"
        },
        "search_text": "cordelia",
        "click_text": "Cordeila Yachting"
    },
    "dream_yacht": {
        "competitor_name": "dream_yacht",
        "yacht_ids": {
            "Aila": "30340400",
            "Elfrith": "10303433",
            "Simply Sale": "40284342",
            "Day Dream": "51286566"
        },
        "search_text": "dream yacht",
        "click_text": "Dream Yacht Charter"
    },
    "eos_yacht": {
        "competitor_name": "eos_yacht",
        "yacht_ids": {
            "Iris": "45049864"
        },
        "search_text": "eos",
        "click_text": "Eos Yacht Charter"
    },
    "just_sail": {
        "competitor_name": "just_sail",
        "yacht_ids": {
            "Just Dream": "31441180"
        },
        "search_text": "just",
        "click_text": "JustSail"
    },
    "love_sail": {
        "competitor_name": "love_sail",
        "yacht_ids": {
            "Sueno": "51665319"
        },
        "search_text": "love",
        "click_text": "LoveSail"
    },
    "miber_sailing": {
        "competitor_name": "miber_sailing",
        "yacht_ids": {
            "whispering_breeze": "39391969",
            "miber_ahren": "39391966",
            "miber_summerbird": "41913854",
            "miber_mars": "32056951",
            "miber_yigit": "32056953",
            "miber_stella": "50541299",
            "okto_sailors": "50541292"
        },
        "search_text": "miber",
        "click_text": "Miber Sailing"
    },
    "most_sailing": {
        "competitor_name": "most_sailing",
        "yacht_ids": {
            "kybele": "51840649"
        },
        "search_text": "most",
        "click_text": "Most Sailing"
    },
    "nautice_alliance": {
        "competitor_name": "nautice_alliance",
        "yacht_ids": {
            "4-friends": "10379823",
            "regulus": "23194693"
        },
        "search_text": "nautic",
        "click_text": "Nautic Alliance"
    },
    "navigare_yachting": {
        "competitor_name": "navigare_yachting",
        "yacht_ids": {
            "west": "33096701"
        },
        "search_text": "navigare",
        "click_text": "Navigare Yachting"
    },
    "pronto_sail": {
        "competitor_name": "pronto_sail",
        "yacht_ids": {
            "pronto_sail": "44996407"
        },
        "search_text": "pronto",
        "click_text": "Pronto Sail"
    },
    "saysail": {
        "competitor_name": "saysail",
        "yacht_ids": {
            "yassica": "23457302",
            "gemile": "31830620",
            "patara": "23457199"
        },
        "search_text": "saysail",
        "click_text": "SAYSAIL"
    },
    "tyc": {
        "competitor_name": "tyc",
        "yacht_ids": {
            "serenity_bellagio": "39454082"
        },
        "search_text": "tyc",
        "click_text": "TYC Serenity"
    }
}

COMMON_CONFIG = {
    "url": "https://portal.booking-manager.com/wbm2/page.html",
    "params": {
        "responseType": "JSON",
        "view": "BookingSheetData",
        "companyid": "7351",
        "timeZoneOffsetInMins": "-60",
        "daily": "false",
        "filter_discounts": "false",
        "isOnHubSpot": "false",
        "isFiltering": "1",
        "resultsPage": "1",
        "filterlocationdistance": "5000",
        "filter_year": "2025",
        "filter_month": "2",
        "filter_date": "23",
        "filter_duration": "7",
        "filter_flexibility": "closest_day",
        "filter_service_type": "all",
        "filter_length_ft": "0-2000",
        "filter_cabins": "0-2000",
        "filter_berths": "0-2000",
        "filter_heads": "0-2000",
        "filter_price": "0-10001000",
        "filter_availability_status": "-1"
    }
}


COMPETITORS_MMK = {
    "sailamor": {
        "competitor_name": "sailamor",
        "url": COMMON_CONFIG["url"],
        "params": {
            **COMMON_CONFIG["params"],
            "from": "1743202800000",
            "to": "1775253599059",
            "fromFormatted": "2025-03-22 00:00",
            "toFormatted": "2026-03-27 23:59",
            "filter_service": "7327",
        },
        "yacht_ids": {
            "Athena 2": "6202735380000107327",
            "Athena 4": "6202765920000107327",
            "Athena 5": "6202767850000107327",
            "Moana": "6202729960000107327",
            "Moana 2": "6202733260000107327",
        },
        "search_text": "Sailamor",
        "click_text": "Sailamor"
    },
    "rudder": {
        "competitor_name": "rudder",
        "url": COMMON_CONFIG["url"],
        "params": {
            **COMMON_CONFIG["params"],
            "from": "1742598000000",
            "to": "1774652399059",
            "fromFormatted": "2025-03-22 00:00",
            "toFormatted": "2026-03-27 23:59",
            "filter_service": "5316",
        },
        "yacht_ids": {
            "Mizu": "4844281322705316",
            "Mithra": "3787149180000105316",
        },
        "search_text": "rudder",
        "click_text": "Rudder&Moor"
    },
    "asmira": {
        "competitor_name": "asmira",
        "url": COMMON_CONFIG["url"],
        "params": {
            **COMMON_CONFIG["params"],
            "from": "1742598000000",
            "to": "1774652399059",
            "fromFormatted": "2025-03-22 00:00",
            "toFormatted": "2026-03-27 23:59",
            "filter_service": "5370",
        },
        "yacht_ids": {
            "Pamina": "3815707090000105370"
        },
        "search_text": "asmira",
        "click_text": "Asmira Marine Yacht Charter"
    },
    "eos": {
        "competitor_name": "eos",
        "url": COMMON_CONFIG["url"],
        "params": {
            **COMMON_CONFIG["params"],
            "from": "1742598000000",
            "to": "1774652399059",
            "fromFormatted": "2025-03-22 00:00",
            "toFormatted": "2026-03-27 23:59",
            "filter_service": "7011",
        },
        "yacht_ids": {
            "Iris": "5756265020000107011"
        },
        "search_text": "eos",
        "click_text": "Eos Yacht Charter"
    },
    "just_sail": {
        "competitor_name": "just_sail",
        "url": COMMON_CONFIG["url"],
        "params": {
            **COMMON_CONFIG["params"],
            "from": "1742598000000",
            "to": "1774652399059",
            "fromFormatted": "2025-03-22 00:00",
            "toFormatted": "2026-03-27 23:59",
            "filter_service": "5349",
        },
        "yacht_ids": {
            "Just Dream": "4321063120000105349",
        },
        "search_text": "just",
        "click_text": "Just Sail"


    },
    "most_sail": {
        "competitor_name": "most_sail",
        "url": COMMON_CONFIG["url"],
        "params": {
            **COMMON_CONFIG["params"],
            "from": "1742598000000",
            "to": "1774652399059",
            "fromFormatted": "2025-03-22 00:00",
            "toFormatted": "2026-03-27 23:59",
            "filter_service": "4371",
        },
        "yacht_ids": {
            "Kybele": "6092161172204371",
        },
        "search_text": "most",
        "click_text": "Most Sail"
    },
    # "love_sail": {},
    # "saysail": {},
}


