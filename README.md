# ONEBOX — Cyber Network Lab for Android

ONEBOX is the Android-facing cyber/network lab inside the university project repository. The Flutter UI is Arabic RTL and uses a dark purple operations-console style.

## Current Android modules

- **MikroTik Lab:** performs a TCP reachability check against a user-entered host and port. This is only a port-connectivity check; it does not authenticate to RouterOS or change router settings.
- **Packet Inspector:** parses the five-byte record header of pasted hexadecimal TLS data as an educational first-pass inspection. It is not a live packet capture engine or a complete PCAP parser.
- **TLS Certificate Lab:** opens a normal TLS connection with platform certificate validation and displays public certificate details.
- **Cyber Toolkit:** lists current diagnostic modules and clearly marks modules that are planned, not implemented.

## Build APK

Open [GitHub Actions](https://github.com/alshmryantqam-debug/SA/actions/workflows/android-app.yml), run the workflow on `main` or push a change under `mobile/`. A successful run uploads the `onebox-android-apk` artifact containing `app-release.apk`.

## Security and scope

- Only test routers and systems you own or are explicitly authorized to assess.
- TCP port reachability is not equivalent to a successful RouterOS API session.
- TLS certificate inspection does not decrypt HTTPS payloads. Capturing encrypted TLS traffic alone does not reveal its plaintext; decryption requires appropriate session secrets or keys in an authorized lab.
- Full RouterOS API management, live capture, PCAP import/analysis, DNS diagnostics, and subscriber/queue views are **not implemented yet** and must not be treated as working features.
- Do not commit router passwords, API tokens, session secrets, or private keys.

## Android source and tests

- App: `mobile/lib/main.dart`
- Widget test: `mobile/test/widget_test.dart`
- Build workflow: `.github/workflows/android-app.yml`

The desktop Python/ADB audit components in this repository remain separate from this Android app.
