def pretty_date(year, day, month):
    import datetime


    date_obj = datetime.date(year, month, day)
    form = "%dth of %B, %Y"
    if str(day)[-1] == '1':
        form = "%dst of %B, %Y"
    elif str(day)[-1] == '2':
        form = "%dnd of %B, %Y"

    formatted_date = date_obj.strftime(form)  # e.g. '24th of December'

    return formatted_date

if __name__ == '__main__':
    pretty_date(2020, 21, 12)