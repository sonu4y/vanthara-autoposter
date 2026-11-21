# VanThara auto-poster

Daily 11:30 IST: reel -> YouTube Short + Instagram Reel. Daily 6:00 PM IST: Instagram photo carousel.
Photos come from vantharahomestay.com automatically. Content plan is in content.py (15 topics: Ramoji Film City,
Wonderla, waterfalls, airport/ORR, TCS Adibatla, birthdays, pre-wedding, etc.). Add more any time.

## Test locally
pip install -r requirements.txt   (ffmpeg must be installed)
python run.py --kind reel --dry-run          # renders out/<item>.mp4 using real site photos

## One-time setup (cannot be done for you - these are your accounts)
### Instagram (Reels + carousels)  [updated: uses 'API setup with Instagram login']
0. Easiest route: Meta app > Instagram > API setup with Instagram login > Add account > Generate token. Copy the Instagram user ID and token shown there. (Account needs the Instagram Tester role on the app.)
(Older Facebook-login route below still works: set IG_GRAPH_HOST=https://graph.facebook.com)
1. Instagram must be a Business or Creator account, linked to a Facebook Page.
2. developers.facebook.com -> create app (Business type) -> add "Instagram Graph API".
3. Graph API Explorer: generate a User token with instagram_basic, instagram_content_publish, pages_show_list,
   pages_read_engagement. Exchange it for a long-lived token (60 days; renew before expiry).
4. Get your IG_USER_ID: GET /me/accounts -> page id -> GET /{page-id}?fields=instagram_business_account
### YouTube
1. console.cloud.google.com -> new project -> enable "YouTube Data API v3".
2. OAuth consent screen (External, add yourself as test user) -> Credentials -> OAuth client ID (Desktop).
3. Run the OAuth flow once (scope youtube.upload) to get a refresh token (e.g. Google's OAuth Playground with your own client ID/secret).
4. IMPORTANT: API uploads from new unaudited projects are forced to PRIVATE. Submit the YouTube API Compliance Audit
   form so uploads can be public. Until then, videos land private and you flip them to Public in Studio.
### Run it free in the cloud (GitHub Actions)
1. Push this folder to a GitHub repo (private is fine).
2. Settings -> Secrets and variables -> Actions -> add: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, IG_USER_ID, IG_ACCESS_TOKEN
3. Actions tab -> "VanThara auto-post" -> Run workflow (kind=reel) to test.

## Music
Drop royalty-free .mp3 files in music/ (YouTube Audio Library). Without music, reels are silent.
Do not use copyrighted songs - the video can be muted/blocked.
