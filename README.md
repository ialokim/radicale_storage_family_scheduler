# Family Scheduler for [Radicale](http://radicale.org/)

This is an storage plugin for Radicale which enables some basic scheduling
operations as in [RFC6638](https://tools.ietf.org/html/rfc6638) (Scheduling
Extensions to CalDAV). Because scheduling is not supported out-of-the-box
(and will probably never be), it was necessary to hack a little bit and
inherit from the storage backend in order to catch up CalDAV events.

The functionality of this plugin is primarily intended for private calendar
servers (e.g. for the family or for little teams), where all users to invite
are using the same Radicale server.

When using this plugin, Radicale will:

* auto-detect attendees in events
* automatically accept the "invitations" from users on the same server
* automatically add the event to the attendees' default calendar

This should work as expected, at least with the already tested clients:

* [Thunderbird](https://www.mozilla.org/en-US/thunderbird/)
* [DAVdroid](https://www.davdroid.com/)

__Caution!__ This plugin does NOT:

* implement the sending of e-mails to attendees outside of the server
* implement the whole specication (RFC6638), only as much as needed

## Installation

In the main folder of the plugin:

`pip install -e .`

## Configuration

This plugin assumes only authenticated users are allowed to connect to Radicale,
so make sure to correctly set the Radicale `auth` backend accordingly.
Please refer to the [Radicale docs](http://radicale.org/configuration/#auth) for more information.

In order to call the plugin, you need to set the storage type to
`radicale_storage_family_scheduler` in the [configuration](http://radicale.org/configuration/).

In addition to this Radicale config, you need to symlink to the default calendar
of each user from a collection called `.Radicale.private`. This calendar will
be used by the plugin for adding events automatically.

## Licence

This plugin is licensed under [Creative Commons Attribution-ShareAlike 4.0 International License](LICENSE.md).
