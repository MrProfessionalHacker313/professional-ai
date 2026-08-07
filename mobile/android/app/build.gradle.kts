plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.professionalai.mobile"
    compileSdk = 34
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    defaultConfig {
        applicationId = "com.professionalai.mobile"
        minSdk = 21
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
        multiDexEnabled = true
    }

    signingConfigs {
        create("release") {
            if (project.hasProperty("ANDROID_KEYSTORE_PATH")) {
                storeFile = file(project.property("ANDROID_KEYSTORE_PATH") as String)
                storePassword = project.property("ANDROID_KEYSTORE_PASSWORD") as String
                keyAlias = project.property("ANDROID_KEY_ALIAS") as String
                keyPassword = project.property("ANDROID_KEY_PASSWORD") as String
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    flavorDimensions += "version"
    productFlavors {
        create("prod") {
            dimension = "version"
            applicationIdSuffix = ""
            manifestPlaceholders["appName"] = "Professional AI"
        }
    }
}

flutter {
    source = "../.."
}
