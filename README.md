# Joaoapps Join (HACS)

Custom integration that replaces the core `joaoapps_join` component.

## Install

1. In Home Assistant open **HACS**, click the **⋮** menu (top right) and choose **Custom repositories**.
2. Enter `https://github.com/surge919/hass_join_update`, set **Type** to **Integration**, and click **Add**.
3. Find **Joaoapps Join** in HACS, click **Download**, then restart Home Assistant.
   - If you previously copied this integration into `config/custom_components/joaoapps_join`, delete that folder first.

## Add your devices

1. Go to **Settings → Devices & services → Joaoapps Join** and click **Add entry**.
2. Enter your Join **API key** (shown at https://joinjoaomgcd.appspot.com/) and click **Submit**.
3. On **Select devices**, optionally set a **Name**, tick the devices to target, and click **Submit**.
   - The name is used as the action prefix and the notify name, e.g. `Pixel 10a` gives `joaoapps_join.pixel_10a_send_url` and `notify.pixel_10a`.

Repeat for each group of devices you want as a separate entry.

## Actions

For an entry named `pixel_10a`:

| Action | Fields |
| --- | --- |
| `joaoapps_join.pixel_10a_ring` | none |
| `joaoapps_join.pixel_10a_send_url` | `url` |
| `joaoapps_join.pixel_10a_send_file` | `url` |
| `joaoapps_join.pixel_10a_set_wallpaper` | `url` |
| `joaoapps_join.pixel_10a_send_sms` | `number`, `message` |
| `joaoapps_join.pixel_10a_send_tasker` | `command` |
| `notify.pixel_10a` | message, title, optional `data` (icon, sound, tts, ...) |

Example:

```yaml
action: joaoapps_join.pixel_10a_send_url
data:
  url: https://home-assistant.io
```
