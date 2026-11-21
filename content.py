"""Content plan. Each item becomes one reel/short or one carousel.
Add your own distances (e.g. '25 min') in `extra` once you've checked them on Google Maps -
nothing here states a distance on purpose."""
from config import PHONE, SITE, LOCATION

BASE_TAGS = "#VanThara #VanTharaHomestay #HyderabadHomestay #VillaStay #HyderabadVilla #WeekendGetaway #Hyderabad"

ITEMS = [
    # ---- nearby attractions ----
    dict(id="ramoji", title="Visiting Ramoji Film City? Stay here", lines=["Ramoji Film City day trip?", "Come back to a private 5BHK villa", "Near Hyderabad ORR"],
         photos=["villa-exterior-corner-view", "home-theater-living-room", "rooftop-terrace", "gallery-lounge", "bedroom-wooden-bed"],
         body="Spending the day at Ramoji Film City? End it in your own private 5-bedroom villa near Hyderabad - home theatre, rooftop terrace, gym and room for 15+ guests.",
         tags="#RamojiFilmCity #RamojiFilmCityHyderabad #HyderabadTrip"),
    dict(id="wonderla", title="Wonderla day + a villa to relax in", lines=["Wonderla with family?", "Entire villa. 15+ guests.", "Day-use & overnight"],
         photos=["grand-entrance-gate", "living-room-decor-globe", "gallery-staircase", "upstairs-lounge-area", "rooftop-terrace"],
         body="Planning a Wonderla day with family or friends? Make it a full getaway - book the whole villa, day-use (4/8/12 hrs) or overnight.",
         tags="#Wonderla #WonderlaHyderabad #FamilyTrip #HyderabadThingsToDo"),
    dict(id="waterfalls", title="Waterfall weekend trips from Hyderabad", lines=["Monsoon waterfall trip?", "Base yourself in a private villa", "Hot water + 24/7 power backup"],
         photos=["villa-exterior-corner-view", "gallery-bedroom", "bedroom-with-ac-and-shelves", "gallery-kitchen", "rooftop-terrace"],
         body="Chasing waterfalls and weekend drives around Hyderabad? Come back to AC bedrooms, a full kitchen, hot water and power backup.",
         tags="#Waterfalls #TelanganaTourism #WeekendDrive #HyderabadWeekend"),
    dict(id="airport", title="Near Hyderabad airport & ORR", lines=["Layover or late flight?", "Easy access via ORR", "Private villa, not a hotel room"],
         photos=["grand-entrance-gate", "ground-floor-dining-staircase", "bedroom-wooden-bed", "gallery-bedroom", "gallery-lounge"],
         body="Easy access to the Outer Ring Road and Rajiv Gandhi International Airport. Ask us on WhatsApp for route guidance.",
         tags="#HyderabadAirport #RGIA #ORR #TravelHyderabad"),
    dict(id="corporate", title="Corporate offsite villa near TCS Adibatla", lines=["Team offsite?", "Near TCS Adibatla & Tata Aerospace SEZ", "WiFi, kitchen, lounge, gym"],
         photos=["gallery-lounge", "upstairs-lounge-area", "gallery-kitchen", "private-gym-room", "rooftop-terrace"],
         body="Offsites, team retreats and working weekends near Adibatla - high-speed WiFi, lounge spaces, professional kitchen and a gym.",
         tags="#CorporateOffsite #TeamOuting #Adibatla #WorkFromVilla"),
    # ---- occasions ----
    dict(id="birthday", title="Birthday party venue in Hyderabad", lines=["Birthday party?", "Home theatre + rooftop + lounge", "Book the whole villa"],
         photos=["rooftop-terrace", "home-theater-living-room", "gallery-lounge", "living-room-decor-globe", "ground-floor-dining-staircase"],
         body="Host birthdays in a private villa: 75-inch 4K home theatre, rooftop terrace and space for 15+ guests.",
         tags="#BirthdayParty #BirthdayVenue #PartyVilla #HyderabadParty"),
    dict(id="prewedding", title="Pre-wedding shoot location in Hyderabad", lines=["Pre-wedding shoot?", "Stairs, fountain, rooftop, decor", "Private & undisturbed"],
         photos=["indoor-water-fountain-closeup", "gallery-staircase", "ganesha-idol-lobby", "rooftop-terrace", "living-room-decor-globe"],
         body="A private villa for pre-wedding and photo shoots - elegant staircases, a water fountain, decor corners and a rooftop terrace.",
         tags="#PreWeddingShoot #PreWeddingLocation #PhotoShootLocation #HyderabadWedding"),
    dict(id="family", title="Family reunion villa for 15+ guests", lines=["Family reunion?", "5 bedrooms, 3 floors", "One villa for everyone"],
         photos=["villa-exterior-corner-view", "ground-floor-dining-staircase", "gallery-kitchen", "bedroom-wooden-bed", "upstairs-lounge-area"],
         body="Everyone under one roof: 5 AC bedrooms across 3 floors, a big kitchen, lounges and balconies on every floor.",
         tags="#FamilyReunion #FamilyGetaway #GroupStay #BigFamily"),
    dict(id="staycation", title="Staycation in Hyderabad - private villa", lines=["Need a break from the city?", "Staycation in your own villa", "Overnight or day-use"],
         photos=["rooftop-terrace", "bedroom-with-ac-and-shelves", "gallery-bedroom", "home-theater-living-room", "private-gym-room"],
         body="Skip the crowded resort. Book the whole villa for a quiet staycation - overnight or 4/8/12-hour day-use blocks.",
         tags="#Staycation #HyderabadStaycation #Getaway #Relax"),
    # ---- villa features ----
    dict(id="theatre", title="75-inch 4K home theatre villa", lines=["75\" 4K home theatre", "Surround sound", "Movie night, anyone?"],
         photos=["home-theater-living-room", "gallery-lounge", "living-room-decor-globe", "upstairs-lounge-area", "gallery-staircase"],
         body="A 75-inch 4K home theatre with surround sound - movie nights with the whole group.", tags="#HomeTheatre #MovieNight #VillaLife"),
    dict(id="rooftop", title="Rooftop terrace evenings", lines=["Rooftop terrace", "Evenings hit different", "Private. Yours."],
         photos=["rooftop-terrace", "villa-exterior-corner-view", "upstairs-lounge-area", "gallery-lounge", "grand-entrance-gate"],
         body="Golden-hour evenings on a private rooftop terrace.", tags="#Rooftop #RooftopVibes #SunsetViews"),
    dict(id="gym", title="Villa with a private gym", lines=["Private gym inside the villa", "Stay fit while you stay", "Gym access on upper floor"],
         photos=["private-gym-room", "upstairs-lounge-area", "bedroom-with-ac-and-shelves", "gallery-bedroom", "rooftop-terrace"],
         body="A private gym for guests - no need to skip workouts on holiday.", tags="#VillaGym #FitnessTravel #StayFit"),
    dict(id="kitchen", title="Professional kitchen for group cooking", lines=["Professional kitchen", "Bosch dishwasher + RO water", "Cook together, eat together"],
         photos=["gallery-kitchen", "ground-floor-dining-staircase", "gallery-lounge", "living-room-decor-globe", "gallery-staircase"],
         body="A professional kitchen with Bosch dishwasher and RO water - perfect for group cooking and celebrations.", tags="#VillaKitchen #GroupCooking #HomeCooked"),
    dict(id="bedrooms", title="5 AC bedrooms across 3 floors", lines=["5 bedrooms", "AC in every room", "King bed. Teak bed. Balconies."],
         photos=["bedroom-wooden-bed", "bedroom-with-ac-and-shelves", "gallery-bedroom", "upstairs-lounge-area", "gallery-staircase"],
         body="Master suite with king bed, teak-bed guest room and two upper-floor rooms with a private lounge and balcony views.", tags="#BedroomGoals #LuxuryVilla #SleepWell"),
    dict(id="walkthrough", title="Villa tour - VanThara Homestay", lines=["Welcome to VanThara", "Entire 5BHK villa", "Turkayamjal, Hyderabad"],
         photos=["grand-entrance-gate", "ground-floor-dining-staircase", "ganesha-idol-lobby", "gallery-lounge", "rooftop-terrace"],
         body="Take a quick tour of VanThara Homestay - a private 5-bedroom villa for families, friends and teams.", tags="#VillaTour #HomestayTour #NewVilla"),
]


def caption(item, platform):
    cta = f"Book the whole villa - WhatsApp {PHONE}\n{SITE}"
    tags = f"{item['tags']} {BASE_TAGS}"
    if platform == "youtube":
        return f"{item['body']}\n\n{cta}\n📍 {LOCATION}\n\n{tags} #Shorts"
    return f"{item['body']}\n\n{cta}\n📍 {LOCATION}\n.\n{tags}"


def yt_title(item):
    t = item["title"]
    return (t[:88] + " #Shorts") if len(t) > 88 else t + " #Shorts"
