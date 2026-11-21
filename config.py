"""Settings for VanThara Homestay auto-poster. Edit freely."""
SITE = "https://vantharahomestay.com"
PHONE = "+91 77357 26603"
WHATSAPP = "https://wa.me/917735726603"
LOCATION = "Turkayamjal, Hyderabad"

# Photos known on the site (the scraper also discovers new ones automatically).
FALLBACK_PHOTOS = [
    "grand-entrance-gate.jpeg", "ground-floor-dining-staircase.jpeg", "ganesha-idol-lobby.jpeg",
    "rooftop-terrace.jpeg", "home-theater-living-room.jpeg", "gallery-staircase.jpg",
    "gallery-bedroom.jpg", "gallery-kitchen.jpg", "gallery-lounge.jpg", "private-gym-room.jpeg",
    "bedroom-with-ac-and-shelves.jpeg", "bedroom-wooden-bed.jpeg", "upstairs-lounge-area.jpeg",
    "living-room-decor-globe.jpeg", "indoor-water-fountain-closeup.jpeg", "villa-exterior-corner-view.jpeg",
]
# Never use these as post photos
SKIP_PHOTOS = {"og-image.jpg", "logo-landscape.jpg", "logo-mark.png"}

REEL_SECONDS_PER_PHOTO = 3.0
REEL_PHOTOS = 5
MUSIC_DIR = "music"      # drop royalty-free .mp3 files here (optional)
