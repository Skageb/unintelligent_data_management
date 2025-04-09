from pymongo.collection import Collection

def run_summaries(db):
    gtd = db["gtd"]

    # fatalities
    print("Updating fatalities_summary...")
    fatalities = list(gtd.aggregate([
        {
            "$group": {
                "_id": "$year",
                "fatalities": {"$sum": {"$toInt": "$fatalities"}}
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$setWindowFields": {
                "partitionBy": None,
                "sortBy": {"_id": 1},
                "output": {
                    "cumulative_fatalities": {
                        "$sum": "$fatalities",
                        "window": {"documents": ["unbounded", "current"]}
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "year": "$_id",
                "fatalities": "$cumulative_fatalities"
            }
        }
    ]))
    db["fatalities_summary"].delete_many({})
    if fatalities:
        db["fatalities_summary"].insert_many(fatalities)

    # ransom by country
    print("Updating ransom_by_country...")
    ransom = list(gtd.aggregate([
        {"$match": {"ransom_demanded": {"$ne": "0"}}},
        {
            "$group": {
                "_id": {
                    "year": "$year",
                    "country": "$country",
                    "country_txt": "$country_txt"
                },
                "ransom_demanded": {"$sum": {"$toInt": "$ransom_demanded"}},
                "ransom_paid": {"$sum": {"$toInt": "$ransom_paid"}}
            }
        },
        {"$sort": {"_id.country": 1, "_id.year": 1}},
        {
            "$setWindowFields": {
                "partitionBy": {"country": "$_id.country", "country_txt": "$_id.country_txt"},
                "sortBy": {"_id.year": 1},
                "output": {
                    "cumulative_ransom_demanded": {
                        "$sum": "$ransom_demanded",
                        "window": {"documents": ["unbounded", "current"]}
                    },
                    "cumulative_ransom_paid": {
                        "$sum": "$ransom_paid",
                        "window": {"documents": ["unbounded", "current"]}
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "year": "$_id.year",
                "country": "$_id.country",
                "country_txt": "$_id.country_txt",
                "ransom_demanded": "$cumulative_ransom_demanded",
                "ransom_paid": "$cumulative_ransom_paid"
            }
        }
    ]))
    db["ransom_by_country"].delete_many({})
    if ransom:
        db["ransom_by_country"].insert_many(ransom)

    # terror by country
    print("Updating terror_by_country...")
    terror_by_country = list(gtd.aggregate([
        {
            "$group": {
                "_id": {
                    "year": "$year",
                    "country": "$country",
                    "country_txt": "$country_txt"
                },
                "number_of_attacks": {"$sum": 1}
            }
        },
        {"$sort": {"_id.country": 1, "_id.year": 1}},
        {
            "$setWindowFields": {
                "partitionBy": {
                    "country": "$_id.country",
                    "country_txt": "$_id.country_txt"
                },
                "sortBy": {"_id.year": 1},
                "output": {
                    "cumulative_attacks": {
                        "$sum": "$number_of_attacks",
                        "window": {"documents": ["unbounded", "current"]}
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "year": "$_id.year",
                "country": "$_id.country",
                "country_txt": "$_id.country_txt",
                "number_of_attacks": "$cumulative_attacks"
            }
        }
    ]))

    db["terror_by_country"].delete_many({})
    if terror_by_country:
        db["terror_by_country"].insert_many(terror_by_country)


    # weapon type summary
    print("Updating weapon_type_summary...")
    weapon = list(gtd.aggregate([
        {
            "$group": {
                "_id": {
                    "year": "$year",
                    "weapon_type": "$weapon_type",
                    "weapon_type_txt": "$weapon_type_txt"
                },
                "fatalities": {"$sum": {"$toInt": "$fatalities"}},
                "wounded": {"$sum": {"$toInt": "$wounded"}},
                "occurences": {"$sum": 1}
            }
        },
        {"$sort": {"_id.weapon_type": 1, "_id.year": 1}},
        {
            "$setWindowFields": {
                "partitionBy": {"weapon_type": "$_id.weapon_type", "weapon_type_txt": "$_id.weapon_type_txt"},
                "sortBy": {"_id.year": 1},
                "output": {
                    "cum_fatalities": {
                        "$sum": "$fatalities",
                        "window": {"documents": ["unbounded", "current"]}
                    },
                    "cum_wounded": {
                        "$sum": "$wounded",
                        "window": {"documents": ["unbounded", "current"]}
                    },
                    "cum_occurences": {
                        "$sum": "$occurences",
                        "window": {"documents": ["unbounded", "current"]}
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "year": "$_id.year",
                "weapon_type": "$_id.weapon_type",
                "weapon_type_desc": "$_id.weapon_type_txt",
                "fatalities": "$cum_fatalities",
                "wounded": "$cum_wounded",
                "occurences": "$cum_occurences"
            }
        }
    ]))
    db["weapon_type_summary"].delete_many({})
    if weapon:
        db["weapon_type_summary"].insert_many(weapon)

    print("All cumulative summary tables updated.\n")
