# Lookitup Android

Native Android client for the Lookitup FastAPI backend.

## What Works

- View trusted sources.
- Load sample sources.
- Add manual, RSS, website, or PDF sources.
- Filter RSS ingestion by optional date range.
- Search a topic inside trusted sources.
- Review Trusted Result Cards.
- Generate an optional grounded summary from current results.

## Run With Android Studio

1. Start the backend:

```bash
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

2. Open this `android/` directory in Android Studio.

3. Run the `app` configuration.

The default API base URL is:

```text
http://10.0.2.2:8000/
```

That works for the Android emulator. For a real Android phone, use the computer's LAN IP.
In Android Studio, add this Gradle property to the run configuration:

```text
-PLOOKITUP_API_BASE_URL=http://192.168.x.x:8000/
```

If Gradle is installed on your machine, the equivalent command is:

```bash
./gradlew :app:installDebug -PLOOKITUP_API_BASE_URL=http://192.168.x.x:8000/
```

The phone and the computer must be on the same network, and the backend must be started with `--host 0.0.0.0`.

## Demo With Web Frontend

Use one backend for both the browser and Android:

```text
FastAPI backend  http://localhost:8000
Web frontend     http://localhost:5173
Android emulator http://10.0.2.2:8000 -> same backend
```

Start the backend first, then run the web frontend from `frontend/` with
`npm run dev`, and finally launch the Android app on the emulator.

## Project Shape

```text
android/
  app/
    src/main/java/com/lookitup/mobile/
      data/        Retrofit API client and DTOs
      ui/          Jetpack Compose screens and ViewModel
      MainActivity.kt
```
