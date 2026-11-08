# Security

Device Proxy passes data and commands to real devices, including writes to inverters and heat
pumps, so problems in it can matter outside the computer.

## Reporting a problem

Please do not open a public issue. Use **Report a vulnerability** on the
[Security tab](https://github.com/bertel2020/HA-Device-Proxy/security) of this repository, so
it stays private until a fix is out. English or German are both fine.

Helpful to know: the app version, the kind of connection, how to reproduce it and what an
attacker would need (access to the LAN, to a client's address, to Home Assistant).

This is a project run in spare time without guaranteed response times. Only the latest version
gets fixes.

## What counts

For example: a client that writes to a Modbus device although its rules forbid it, getting past
the allowed networks or a block, reaching the web interface or ser2net's admin interface without
going through Home Assistant, a configuration or an import that runs commands, or diagnostics
that give away what they say they leave out.

## What is known and by design

- The device ports are plain TCP without a login or encryption, as the protocols are. Who may
  connect is limited by address only (**Settings → Network** and each connection's rules), and an
  address can be forged inside a network. Do not expose these ports to the internet; use a VPN.
- With **Own file** under **Settings → ser2net.yaml**, your own file runs as it is and can do
  whatever ser2net can, including starting programs. Whoever can write the app's config folder can
  do that as well.
- A backup file contains the MQTT login.
