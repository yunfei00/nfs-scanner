# Release Process

## 1. Goal

A release should be reproducible and suitable for offline customer deployment.

## 2. Release Types

- Development build
- Demo build
- Internal test build
- Customer delivery build

## 3. Pre-release Checklist

- Product spec is up to date.
- Architecture decisions are documented.
- App starts on a clean machine.
- Example project opens.
- Mock scan workflow works.
- Device connection errors are user-friendly.
- Logs are written to expected location.
- Version number is updated.

## 4. Customer Delivery Checklist

- Offline package or installer is created.
- Required drivers or runtime notes are documented.
- Example data is included if allowed.
- User guide is included.
- Known limitations are listed.

## 5. Future Packaging Targets

- PyInstaller one-folder build
- PyInstaller one-file build
- Windows installer
- Green portable package

## 6. Versioning

Suggested version format:

- `0.x` for internal development
- `1.0` for first commercial-ready version
- patch versions for bug fixes

## 7. Release Notes

Each release note should include:

- new features
- fixed issues
- known limitations
- compatibility notes
- upgrade notes
