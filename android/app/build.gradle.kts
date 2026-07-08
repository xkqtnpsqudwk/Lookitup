plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

val configuredApiBaseUrl = providers
    .gradleProperty("LOOKITUP_API_BASE_URL")
    .orElse("http://10.0.2.2:8000/")
    .get()
    .let { value -> if (value.endsWith("/")) value else "$value/" }
    .replace("\\", "\\\\")
    .replace("\"", "\\\"")

android {
    namespace = "com.lookitup.mobile"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.lookitup.mobile"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"

        buildConfigField("String", "API_BASE_URL", "\"$configuredApiBaseUrl\"")
    }

    buildFeatures {
        buildConfig = true
        compose = true
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2026.04.00"))
    implementation("androidx.activity:activity-compose:1.12.0")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    implementation("com.jakewharton.retrofit:retrofit2-kotlinx-serialization-converter:1.0.0")
    implementation("com.squareup.okhttp3:logging-interceptor:5.1.0")
    implementation("com.squareup.retrofit2:retrofit:3.0.0")

    debugImplementation("androidx.compose.ui:ui-tooling")
}
