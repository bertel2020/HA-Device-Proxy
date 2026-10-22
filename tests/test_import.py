from device_proxy import custom
from device_proxy.config import export
from device_proxy.importer import merge, read
from device_proxy.model import AppConfig, Connection

V1 = """%YAML 1.1
---
define: &banner1 Hallo
default:
  name: local
  value: true
  class: serialdev

connection: &zwave
  accepter: tcp(nodelay),3333
  connector: serialdev,/dev/serial/by-id/usb-Zooz-if00,115200n81
  options:
    max-connections: 2
    kickolduser: true

connection: &ehz
  accepter: tcp,3335
  enable: off
  timeout: 30
  connector: sdev,/dev/serial/by-id/usb-CP2102-if00-port0,9600N81,rtscts,custspeed
  options:
    banner: "*(banner1) eHZ"
    remaddr: 192.168.1.20,0;10.0.0.0/8,1234
    trace-both: /tmp/ehz.trace
    sendon: "\\r\\n"

connection: &secure
  accepter: telnet(rfc2217),mux,certauth,ssl,tcp,4001
  connector: serialdev,/dev/ttyS0,9600n81

admin:
  accepter: tcp,127.0.0.1,2000
"""

V2 = """%YAML 1.1
---
connections:
  bwt:
    accepter: telnet(rfc2217),tcp,192.168.1.10,3334
    connector: serialdev,/dev/serial/by-id/usb-FTDI-if00-port0,19200e71,local,dtr=off
"""


def test_version_1_with_defines_defaults_and_notes() -> None:
    result = read(V1)
    assert result.version == 1
    items = {i.alias: i for i in result.items}
    zwave, ehz, secure = items["zwave"].connection, items["ehz"].connection, items["secure"]
    assert zwave is not None and ehz is not None
    assert (zwave.port, zwave.baud, zwave.nodelay, zwave.max_clients) == (3333, 115200, True, 2)
    assert zwave.local and zwave.kickolduser  # local from the default
    assert (ehz.enabled, ehz.timeout, ehz.rtscts, ehz.trace) == (False, 30, True, "both")
    assert ehz.banner == "Hallo eHZ"
    assert ehz.remaddr == "192.168.1.20/32 10.0.0.0/8"
    assert ehz.extra == (("sendon", "\r\n"),)  # YAML escapes decoded
    codes = {n["code"] for n in items["ehz"].notes}
    assert {"serial_option_dropped", "remaddr_port_dropped", "trace_files_moved"} <= codes
    assert secure.connection is None and secure.notes[0]["code"] == "accepter_unsupported"
    assert {"code": "admin_ignored"} in result.notes


def test_version_2() -> None:
    result = read(V2)
    bwt = result.items[0].connection
    assert result.version == 2 and bwt is not None
    assert (bwt.name, bwt.mode, bwt.bind, bwt.port) == ("bwt", "rfc2217", "192.168.1.10", 3334)
    assert (bwt.baud, bwt.parity, bwt.data_bits, bwt.stop_bits) == (19200, "e", 7, 1)
    assert (bwt.local, bwt.dtr) == (True, "off")


def test_merge_conflicts_and_export_round_trip() -> None:
    existing = Connection("Z-Wave alt", "/dev/ttyACM0", 3333, id="0000000a")
    current = AppConfig(connections=(existing,))
    result = read(V1)
    skipped = merge(current, result, replace_all=False, take={"zwave", "ehz"}, on_conflict={})
    assert [c.name for c in skipped.connections] == ["Z-Wave alt", "ehz"]
    moved = merge(
        current, result, replace_all=False, take={"zwave"}, on_conflict={"zwave": "new_port"}
    )
    assert [c.port for c in moved.connections] == [3333, 3334]
    replaced = merge(
        current, result, replace_all=False, take={"zwave"}, on_conflict={"zwave": "replace"}
    )
    assert [(c.name, c.id) for c in replaced.connections] == [("zwave", "0000000a")]

    again = read(export(replaced))
    back = again.items[0].connection
    assert back is not None and again.items[0].alias == "zwave"
    original = replaced.connections[0]
    for field in ("port", "baud", "nodelay", "max_clients", "kickolduser", "local"):
        assert getattr(back, field) == getattr(original, field), field


def test_own_file_check_and_admin_socket() -> None:
    assert [e["code"] for e in custom.check(V1).errors] == ["admin_present"]
    check = custom.check(V2)
    assert check.ok and check.connections == [{"alias": "bwt", "port": 3334, "enabled": True}]
    text = custom.runtime(V2, check.version)
    assert text.endswith(
        "---\nadmins:\n  device_proxy:\n    accepter: "
        "unix(delsock,umode=6,gmode=0,omode=0),/run/ser2net-admin.sock\n"
    )


LEGACY = """# ser2net 3
BANNER:hello:Hallo \\r\\n
TRACEFILE:t1:/tmp/ehz-\\p.trace
DEVICE:zwave:/dev/serial/by-id/usb-Zooz-if00
DEFAULT:local:true
3333:raw:0:zwave:115200 NONE 1STOPBIT 8DATABITS -LOCAL max-connections=2 kickolduser
3335:telnet:30:/dev/serial/by-id/usb-CP2102-if00-port0:9600 EVEN 7DATABITS remctl \\
  hello tb=t1 RTSCTS
127.0.0.1,3336:off:0:/dev/ttyS1:4800
CONTROLPORT:localhost,2000
"""


def test_old_format() -> None:
    result = read(LEGACY)
    assert result.version == 0
    zwave, ehz, s1 = (i.connection for i in result.items)
    assert zwave is not None and ehz is not None and s1 is not None
    assert (zwave.name, zwave.port, zwave.baud, zwave.local, zwave.kickolduser) == (
        "zwave",
        3333,
        115200,
        False,
        True,
    )
    assert (ehz.mode, ehz.timeout, ehz.parity, ehz.data_bits, ehz.rtscts, ehz.local) == (
        "rfc2217",
        30,
        "e",
        7,
        True,
        True,
    )
    assert (ehz.banner, ehz.trace) == ("Hallo \\r\\n", "both")
    assert (s1.name, s1.bind, s1.port, s1.enabled, s1.baud) == (
        "port 3336",
        "127.0.0.1",
        3336,
        False,
        4800,
    )
    assert {"code": "admin_ignored"} in result.notes
    assert custom.check(LEGACY).errors == [{"code": "legacy_format"}]


def test_ha_modbusproxy_options_become_modbus_connections() -> None:
    text = (
        "devices:\n"
        "  - upstreamhost: 192.168.1.10\n    upstreamport: 502\n    listenport: 502\n"
        "  - upstreamhost: 192.168.1.11\n    upstreamport: 1502\n    listenport: 503\n"
        "    timeout: 5\n    connection_time: 0.1\n"
        "timeout: 10\nloglevel: INFO\n"
    )
    result = read(text)
    first, second = (item.connection for item in result.items)
    assert first and first.kind == "modbus" and first.host == "192.168.1.10"
    assert first.port == 502 and first.request_timeout_ms == 10000
    assert second and (second.host_port, second.port) == (1502, 503)
    assert (second.request_timeout_ms, second.connect_delay_ms) == (5000, 100)
    assert first.write_access == "all"  # as with ha-modbusproxy


def test_modbus_proxy_file_yaml_and_toml() -> None:
    yaml_text = (
        "devices:\n"
        "  - modbus: {url: 'plc1.acme.org:502', timeout: 2}\n"
        "    listen: {bind: ':5020'}\n"
        "    unit_id_remapping: {1: 0}\n"
    )
    toml_text = (
        "[[devices]]\n"
        "modbus = {url = 'tcp://plc1.acme.org:502', timeout = 2}\n"
        "listen = {bind = '0:5020'}\n"
        "unit_id_remapping = {1 = 0}\n"
    )
    for text in (yaml_text, toml_text):
        result = read(text)
        (item,) = result.items
        c = item.connection
        assert c and (c.host, c.host_port, c.port, c.bind) == ("plc1.acme.org", 502, 5020, "")
        assert (c.request_timeout_ms, c.unit_map) == (2000, "1=0")


def test_next_free_port_skips_the_reserved_one_and_the_end_of_the_range() -> None:
    from device_proxy.model import INGRESS_PORT

    text = "connection: &a\n  accepter: tcp,%d\n  connector: serialdev,/dev/ttyUSB0,9600n81\n"
    current = AppConfig(
        connections=(Connection("x", "/dev/ttyX", INGRESS_PORT - 1, id="0000000a"),)
    )
    result = read(text % (INGRESS_PORT - 1))
    alias = result.items[0].alias
    merged = merge(
        current, result, replace_all=False, take={alias}, on_conflict={alias: "new_port"}
    )
    assert INGRESS_PORT not in {c.port for c in merged.connections}
    assert len(merged.connections) == 2
    top = AppConfig(connections=(Connection("x", "/dev/ttyX", 65535, id="0000000a"),))
    result = read(text % 65535)
    alias = result.items[0].alias
    merged = merge(top, result, replace_all=False, take={alias}, on_conflict={alias: "new_port"})
    assert len(merged.connections) == 1  # skipped, not an error


def test_export_without_serial_connections_has_a_commented_example() -> None:
    text = export(AppConfig())
    assert "# connection: &example" in text
    assert "\nconnection:" not in text  # all commented out
    assert "example" not in export(
        AppConfig(connections=(Connection("eHZ", "/dev/ttyUSB0", 3335),))
    )
