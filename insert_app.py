import sqlite3
import time

# Connect to both databases
nova_conn = sqlite3.connect('nova.db')
icons_conn = sqlite3.connect('app_icons.db')

nova_cursor = nova_conn.cursor()
icons_cursor = icons_conn.cursor()

# First add the drawer group for tasky
nova_cursor.execute("""
INSERT INTO drawer_groups (_id, title, groupType, tabOrder, hideApps, tabColor, flags, modified)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    17,
    'soc',
    'FOLDER_APP_GROUP',
    2,
    1,
    262914,
    0,
    int(time.time() * 1000)
))

# Set container ID for soc folder
container_id = -217

# Apps in soc folder - all using container_id -217
apps = [
    ('org.telegram.messenger/org.telegram.messenger.DefaultIcon', 'Telegram'),
    ('com.reddit.frontpage/launcher.default', 'Reddit'),
    ('com.eaglefleet.redtaxi/com.eaglefleet.redtaxi.launcher_alias.RTDefaultLauncherAlias', 'RED Taxi'),
    ('com.jio.myjio/com.jio.myjio.dashboard.activities.SplashActivity', 'MyJio'),
    ('com.truecaller/com.truecaller.ui.TruecallerInit', 'Truecaller'),
    ('com.amazon.avod.thirdpartyclient/com.amazon.avod.thirdpartyclient.LauncherActivity', 'Prime Video'),
    ('com.google.android.googlequicksearchbox/com.google.android.googlequicksearchbox.SearchActivity', 'Google'),
    ('com.google.android.gm/com.google.android.gm.ConversationListActivityGmail', 'Gmail'),
    ('in.gov.umang.negd.g2c/in.gov.umang.negd.g2c.kotlin.ui.splash.UmangLauncherActivity', 'UMANG'),
    ('com.digilocker.android/in.gov.digilocker.views.mainactivity.SplashScreenActivity', 'DigiLocker'),
    ('com.rapido.passenger/com.rapido.passenger.DefaultAlias', 'Rapido')
]

for component_name, title in apps:
    # Get icon blob
    icons_cursor.execute("SELECT icon FROM icons WHERE componentName=? AND profileId=-1", (component_name,))
    result = icons_cursor.fetchone()
    if not result:
        print(f"No icon found for {component_name}, skipping...")
        continue
    icon_blob = result[0]

    # Insert into favorites
    nova_cursor.execute("""
INSERT INTO favorites (
    title,
    intent,
    container,
    screen,
    cellX,
    cellY,
    spanX,
    spanY,
    itemType,
    appWidgetId,
    icon,
    modified,
    restored,
    profileId,
    rank,
    options,
    appWidgetSource,
    zOrder,
    novaFlags
)
VALUES (
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
)""", (
    title,
    f'#Intent;action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;launchFlags=0x10200000;component={component_name};end',
    container_id,
    0,
    0.0,
    0.0,
    1.0,
    1.0,
    0,
    -1,
    icon_blob,
    int(time.time() * 1000),
    0,
    -1,
    0,
    0,
    -1,
    0,
    0
))

    nova_conn.commit()

print("All apps from soc folder have been added!")
nova_conn.close()
icons_conn.close()
