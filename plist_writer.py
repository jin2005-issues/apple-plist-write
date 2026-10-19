#!/usr/bin/env python3
"""
Apple XML Property List (plist) 自动编写工具
支持交互式填写，自动填入合法结构
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, date, time
import uuid
import getpass
import os
import copy
import argparse
import sys
import curses


# ─────────────────────────────────────────────
#  常用 plist 结构模板（自动补全选项）
# ─────────────────────────────────────────────
COMMON_STRUCTURES = {

    # ── iOS / iPadOS Info.plist ─────────────────────────────────
    "info_ios": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "com.example.app",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "LSRequiresIPhoneOS": True,
        "UILaunchStoryboardName": "LaunchScreen",
        "UIApplicationSceneManifest": {
            "UIApplicationSupportsMultipleScenes": False,
            "UISceneConfigurations": {
                "UIWindowSceneSessionRoleApplication": []
            },
        },
        "UIApplicationSupportsIndirectInputEvents": True,
        "UIRequiresFullScreen": False,
        "UIStatusBarStyle": "UIStatusBarStyleDefault",
        "UIUserInterfaceStyle": "Light",
        "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
        "UISupportedInterfaceOrientations~ipad": [
            "UIInterfaceOrientationPortrait",
            "UIInterfaceOrientationPortraitUpsideDown",
            "UIInterfaceOrientationLandscapeLeft",
            "UIInterfaceOrientationLandscapeRight",
        ],
        "UIRequiredDeviceCapabilities": ["armv7"],
        "NSCameraUsageDescription": "此应用需要使用相机",
        "NSPhotoLibraryUsageDescription": "此应用需要访问您的照片",
        "NSPhotoLibraryAddUsageDescription": "此应用需要保存照片到您的相册",
        "NSLocationWhenInUseUsageDescription": "此应用需要您的位置来提供个性化体验",
        "NSLocationAlwaysAndWhenInUseUsageDescription": "此应用需要在后台访问您的位置",
        "NSMicrophoneUsageDescription": "此应用需要使用麦克风",
        "NSFaceIDUsageDescription": "使用 Face ID 解锁内容",
        "NSCalendarsUsageDescription": "此应用需要访问您的日历",
        "NSContactsUsageDescription": "此应用需要访问您的联系人",
        "NSBluetoothAlwaysUsageDescription": "此应用需要蓝牙来连接设备",
        "NSBluetoothPeripheralUsageDescription": "此应用需要蓝牙来连接配件",
        "NSSiriUsageDescription": "此应用使用 Siri 来完成语音指令",
        "ITSAppUsesNonExemptEncryption": False,
        "UILaunchScreen": {
            "UIImageName": "",
            "UIColorName": "",
            "UIImageRespectsSafeAreaInsets": True,
        },
        "UIApplicationShortcutItems": [],
        "UIBackgroundModes": [],
    },

    # ── macOS Info.plist ────────────────────────────────────────
    "info_macos": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "com.example.app",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "$(MACOSX_DEPLOYMENT_TARGET)",
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "Copyright © 2026 YourCompany. All rights reserved.",
        "NSPrincipalClass": "NSApplication",
        "NSMainStoryboardFile": "MainMenu",
        "NSSupportsAutomaticTermination": True,
        "NSSupportsSuddenTermination": True,
        "LSApplicationCategoryType": "public.app-category.productivity",
        "NSCameraUsageDescription": "此应用需要使用相机",
        "NSMicrophoneUsageDescription": "此应用需要使用麦克风",
        "NSAppleEventsUsageDescription": "此应用需要向其他应用发送指令",
        "CFBundleIconFile": "AppIcon",
        "NSDocumentsFolderUsageDescription": "此应用需要访问您的文稿",
    },

    # ── watchOS Info.plist ──────────────────────────────────────
    "info_watchos": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "WKApplication": True,
        "WKCompanionAppBundleIdentifier": "com.example.app",
        "WKRunsIndependentlyOfCompanionApp": False,
        "NSFaceIDUsageDescription": "使用 Face ID 解锁手表内容",
        "NSHealthShareUsageDescription": "此应用需要读取健康数据",
        "NSHealthUpdateUsageDescription": "此应用需要写入健康数据",
        "WKSensorTypes": [],
        "WKHealthThermometerUseDescription": "测量体温",
    },

    # ── watchOS Glance / WatchKit App ───────────────────────────
    "info_watchkit_app": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "BNDL",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "WKCompanionAppBundleIdentifier": "com.example.app",
        "NSExtension": {
            "NSExtensionPointIdentifier": "com.apple.watchkit",
            "NSExtensionPrincipalClass": "$(PRODUCT_MODULE_NAME).GlanceController",
        },
    },

    # ── Widget Extension ────────────────────────────────────────
    "info_widget": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "Widget",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "XPC!",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSExtension": {
            "NSExtensionPointIdentifier": "com.apple.widgetkit-extension",
        },
        "CFBundleDisplayName": "Widget",
    },

    # ── Notification Service Extension ──────────────────────────
    "info_notification_ext": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "NotificationService",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "XPC!",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSExtension": {
            "NSExtensionPointIdentifier": "com.apple.usernotifications.service",
            "NSExtensionPrincipalClass": "$(PRODUCT_MODULE_NAME).NotificationService",
        },
    },

    # ── App Clip ────────────────────────────────────────────────
    "info_appclip": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "App Clip",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "CFBundleResourceSpecificationStyle": "tree",
        "LSRequiresIPhoneOS": True,
        "UILaunchStoryboardName": "LaunchScreen",
        "UIApplicationSceneManifest": {
            "UIApplicationSupportsMultipleScenes": False,
            "UISceneConfigurations": {
                "UIWindowSceneSessionRoleApplication": []
            },
        },
        "NSAppClip": {
            "NSAppClipRequestLocationNotificationAccess": False,
            "NSAppClipRequestsDestinationApp": False,
        },
        "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
    },

    # ── Safari Web Extension ────────────────────────────────────
    "info_safari_ext": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "Safari Extension",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "XPC!",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSExtension": {
            "NSExtensionPointIdentifier": "com.apple.Safari.web-extension",
            "NSExtensionPrincipalClass": "$(PRODUCT_MODULE_NAME).SafariWebExtensionHandler",
        },
        "SFSafariWebExtensionConverterVersion": "16.0",
    },

    # ── Intent Extension (SiriKit) ──────────────────────────────
    "info_intent_ext": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "Intents",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "XPC!",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSExtension": {
            "NSExtensionAttributes": {
                "IntentsSupported": [],
                "IntentsRestrictedWhileLocked": [],
                "IntentsRestrictedWhileProtectedDataUnavailable": [],
            },
            "NSExtensionPointIdentifier": "com.apple.intents-service",
            "NSExtensionPrincipalClass": "$(PRODUCT_MODULE_NAME).IntentHandler",
        },
    },

    # ── Share Extension ─────────────────────────────────────────
    "info_share_ext": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "Share",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "XPC!",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSExtension": {
            "NSExtensionAttributes": {
                "NSExtensionActivationRule": {
                    "NSExtensionActivationSupportsText": True,
                    "NSExtensionActivationSupportsWebURLWithMaxCount": 1,
                    "NSExtensionActivationSupportsImageWithMaxCount": 10,
                    "NSExtensionActivationSupportsMovieWithMaxCount": 1,
                    "NSExtensionActivationSupportsFileWithMaxCount": 10,
                },
            },
            "NSExtensionPointIdentifier": "com.apple.share-services",
            "NSExtensionPrincipalClass": "$(PRODUCT_MODULE_NAME).ShareViewController",
        },
    },

    # ── Photo Editing Extension ─────────────────────────────────
    "info_photo_edit_ext": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleDisplayName": "Photo Edit",
        "CFBundleExecutable": "$(EXECUTABLE_NAME)",
        "CFBundleIdentifier": "$(PRODUCT_BUNDLE_IDENTIFIER)",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "$(PRODUCT_NAME)",
        "CFBundlePackageType": "XPC!",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1",
        "NSExtension": {
            "NSExtensionPointIdentifier": "com.apple.photo-editing",
            "NSExtensionPrincipalClass": "$(PRODUCT_MODULE_NAME).PhotoEditingViewController",
        },
    },

    # ── .entitlements (iOS/macOS 通用) ──────────────────────────
    "entitlements": {
        "com.apple.security.app-sandbox": True,
        "com.apple.security.network.client": True,
        "com.apple.security.network.server": True,
        "com.apple.security.files.user-selected.read-write": True,
        "com.apple.security.files.downloads.read-write": True,
    },

    # ── .entitlements (iCloud) ──────────────────────────────────
    "entitlements_icloud": {
        "com.apple.security.app-sandbox": True,
        "com.apple.developer.icloud-container-identifiers": ["iCloud.com.example.app"],
        "com.apple.developer.icloud-services": ["CloudDocuments", "CloudKit"],
        "com.apple.developer.ubiquity-kvstore-identifier": "$(TeamIdentifierPrefix)com.example.app",
        "com.apple.developer.icloud-document-sync": True,
        "com.apple.developer.icloud-keyvalue-sync": True,
    },

    # ── .entitlements (Push Notifications) ──────────────────────
    "entitlements_push": {
        "aps-environment": "development",
        "com.apple.security.application-groups": ["group.com.example.app"],
        "keychain-access-groups": ["$(AppIdentifierPrefix)com.example.app"],
    },

    # ── .entitlements (App Groups + Keychain) ───────────────────
    "entitlements_app_groups": {
        "com.apple.security.application-groups": ["group.com.example.app"],
        "keychain-access-groups": ["$(AppIdentifierPrefix)com.example.app"],
        "com.apple.developer.associated-domains": ["applinks:example.com"],
    },

    # ── .entitlements (macOS) ───────────────────────────────────
    "entitlements_mac": {
        "com.apple.security.app-sandbox": True,
        "com.apple.security.network.client": True,
        "com.apple.security.network.server": True,
        "com.apple.security.files.user-selected.read-write": True,
        "com.apple.security.files.bookmarks.app-scope": True,
        "com.apple.security.automation.apple-events": True,
        "com.apple.security.temporary-exception.apple-events": [],
    },

    # ── .entitlements (tvOS) ────────────────────────────────────
    "entitlements_tvos": {
        "com.apple.security.app-sandbox": True,
        "com.apple.security.network.client": True,
        "com.apple.security.network.server": True,
        "com.apple.security.files.user-selected.read-write": True,
    },

    # ── iTunes / App Store Sandbox ──────────────────────────────
    "itunes_sandbox": {
        "com.apple.gksandbox": {
            "GKSandboxExtensions": {
                "com.apple.security.application-groups": ["group.com.example.app"],
                "com.apple.developer.storekit.external-purchase": True,
            },
            "GKSandboxMode": "user",
            "GKFeatures": {
                "GameCenter": True,
                "StoreKit": True,
                "iCloud": False,
                "PushNotifications": True,
            },
            "GKTestAccounts": [],
            "GKEnabledDiagnosticModes": ["network", "sandbox"],
        },
        "com.apple.GKSandboxBuddy": {
            "CFBundleIdentifier": "com.apple.GKSandboxBuddy",
            "CFBundleVersion": "1",
            "CFBundleShortVersionString": "1.0",
            "GKApplicationIdentifier": "$(TeamIdentifierPrefix)com.example.app",
            "GKAppStoreReceiptPath": "$(HOME)/Library/Logs/CoreSimulator/receipt",
            "GKEnvironment": "sandbox",
        },
    },

    # ── iTunesMetadata.plist (App Store 提交用) ─────────────────
    "itunes_metadata": {
        "application genres": ["public.app-category.productivity"],
        "application category": "public.app-category.productivity",
        "artistName": "",
        "bundleDisplayName": "",
        "bundleIdentifier": "com.example.app",
        "bundleVersion": "1",
        "copyright": "Copyright © 2026 YourCompany. All rights reserved.",
        "gameCenter": {
            "gc-enabled": True,
            "gc-friends-visible": True,
        },
        "itemName": "",
        "kind": "software",
        "marketingVersion": "1.0.0",
        "playlistGUITrackID": 0,
        "playlistID": 0,
        "rating": {
            "content": "",
            "label": "",
            "rank": 0,
            "system": "itunes-games",
        },
        "softwareVersionExternalIdentifier": 0,
        "softwareVersionBundleId": "com.example.app",
        "storeCohort": {
            "dateKey": "",
            "storeFrontIDs": [],
        },
        "vendorIdentifier": "com.example.app",
        "drmSystemNumber": 0,
        "fileSharing": False,
        "hasSettingsUI": True,
        "hasMagicDock": False,
        "minimumOSVersion": "15.0",
        "minimumSystemVersion": "15.0",
        "supportedPlatforms": ["macOS", "iOS", "iPadOS"],
        "countryCodes": ["CN", "TW", "HK", "US"],
        "isWrapper": False,
        " ISDOCKPODCAST": False,
        "isPromotionVoiceMemo": False,
        "isExplicit": False,
        "isGPSProvidable": False,
        "networkContention": "wifi",
        "requiredDeviceCapabilities": ["arm64"],
        "suggestedSortOrder": "relevance",
        "regionOfDesign": ["CN"],
        "localRegionOfDesign": "CN",
    },

    # ── StoreKit External Purchase (第三方支付沙盒) ─────────────
    "storekit_external_purchase": {
        "com.apple.developer.storekit.external-purchase": True,
        "com.apple.developer.storekit.external-purchase.certificates": [],
        "EXAppStoreExternalPurchaseEntitlements": {
            "Entitlements": [
                {
                    "CertificateID": "",
                    "Environment": "Sandbox",
                    "MerchantID": "merchant.com.example.app",
                    "Enabled": True,
                }
            ]
        },
        "ExternalPurchaseSessionConfig": {
            "SessionTimeout": 300,
            "AllowedExternalPurchaseURLSchemes": ["com.example.app.externalpurchase"],
            "ExternalPurchaseHost": "api.example.com",
        },
    },

    # ── Game Center (Sandbox) ──────────────────────────────────
    "gamecenter_sandbox": {
        "com.apple.game-center": {
            "GCEnabled": True,
            "GCDefaultLeaderboardCategory": "",
            "GCDefaultLeaderboardTimeScope": "all_time",
            "GCAuthenticateLocalUser": True,
            "GCShowFriendsList": True,
            "GCChallengeComposeMaxParticipants": 4,
            "GCChallengeComposeMessageMaxLength": 500,
        },
        "leaderboards": {
            "categories": [
                {
                    "categoryID": "com.example.app.leaderboard",
                    "title": "",
                    "sortOrder": "descending",
                    "startDate": datetime.now().isoformat(),
                    "endDate": None,
                    "scoresToSubmit": 10,
                    "playerScope": "global",
                }
            ]
        },
        "achievements": {
            "definitions": [
                {
                    "achievementID": "com.example.app.achievement.first_win",
                    "title": "首次胜利",
                    "achievedDescription": "恭喜获得首次胜利！",
                    "unachievedDescription": "在对战中取得第一次胜利",
                    "points": 10,
                    "hidden": False,
                }
            ]
        },
    },

    # ── Xcode Build Settings (.xcconfig 风格) ───────────────────
    "build_settings": {
        "PRODUCT_BUNDLE_IDENTIFIER": "com.example.app",
        "PRODUCT_NAME": "$(TARGET_NAME)",
        "TARGETED_DEVICE_FAMILY": "1,2",
        "IPHONEOS_DEPLOYMENT_TARGET": "15.0",
        "MACOSX_DEPLOYMENT_TARGET": "12.0",
        "WATCHOS_DEPLOYMENT_TARGET": "8.0",
        "TVOS_DEPLOYMENT_TARGET": "15.0",
        "SWIFT_VERSION": "5.0",
        "CODE_SIGN_STYLE": "Automatic",
        "CODE_SIGN_IDENTITY": "-",
        "ENABLE_BITCODE": False,
        "DEBUG_INFORMATION_FORMAT": "dwarf-with-dsym",
        "VALID_ARCHS": ["arm64", "x86_64"],
        "BUILD_LIBRARY_FOR_DISTRIBUTION": False,
        "CLANG_ENABLE_MODULES": True,
        "SWIFT_OBJC_BRIDGING_HEADER": "",
        "CLANG_ANALYZER_LOCALIZABILITY_NONLOCALIZED": True,
        "INFOPLIST_FILE": "$(SRCROOT)/$(TARGET_NAME)/Info.plist",
        "ASSETCATALOG_COMPILER_APPICON_NAME": "AppIcon",
        "GENERATE_INFOPLIST_FILE": True,
        "CURRENT_PROJECT_VERSION": 1,
        "MARKETING_VERSION": "1.0.0",
    },

    # ── UIWindowScene 配置 ──────────────────────────────────────
    "scene_config": {
        "UIApplicationSceneManifest": {
            "UIApplicationSupportsMultipleScenes": False,
            "UISceneConfigurations": {
                "UIWindowSceneSessionRoleApplication": [
                    {
                        "UISceneConfigurationName": "Default Configuration",
                        "UISceneDelegateClassName": "$(PRODUCT_MODULE_NAME).SceneDelegate",
                        "UISceneStoryboardFile": "Main",
                    }
                ],
                "UIWindowSceneSessionRoleExternalDisplayNonInteractive": [],
            },
        }
    },

    # ── Asset Catalog Contents.json ─────────────────────────────
    "asset_catalog": {
        "info": {
            "author": "xcode",
            "version": 1,
        },
        "colors": [],
        "images": [],
        "properties": {},
    },

    # ── Swift Package Resolved (.resolved) ──────────────────────
    "swift_resolved": {
        "pins": [
            {
                "package": "",
                "repositoryURL": "",
                "state": {
                    "branch": None,
                    "revision": "",
                    "version": "1.0.0",
                },
            }
        ],
        "version": 2,
    },

    # ── UserDefaults 种子数据 ───────────────────────────────────
    "user_defaults": {
        "username": "",
        "lastLoginDate": datetime.now().isoformat(),
        "sessionToken": str(uuid.uuid4()),
        "preferences": {
            "theme": "auto",
            "notificationsEnabled": True,
            "fontSize": 14,
            "language": "zh-Hans",
        },
        "featureFlags": {
            "enableBeta": False,
            "maxRetryCount": 3,
        },
    },

    # ── NSUserActivity (Handoff / Spotlight) ────────────────────
    "user_activity": {
        "NSUserActivityType": "com.example.app.view",
        "NSUserActivityTitle": "",
        "NSUserActivityURLString": "https://example.com/page",
        "NSUserActivityThumbnailData": None,
        "NSUserActivityKeywords": [],
        "isEligibleForSearch": True,
        "isEligibleForHandoff": True,
        "isEligibleForPublicIndexing": False,
    },

    # ── launchd daemon/agent plist ──────────────────────────────
    "launchd": {
        "Label": "com.example.agent",
        "ProgramArguments": ["/usr/bin/python3", "/path/to/script.py"],
        "RunAtLoad": False,
        "KeepAlive": {"SuccessfulExit": False},
        "StandardOutPath": "/tmp/agent.out.log",
        "StandardErrorPath": "/tmp/agent.err.log",
        "EnvironmentVariables": {"PATH": "/usr/local/bin:/usr/bin:/bin"},
        "ThrottleInterval": 10,
        "ProcessType": "Interactive",
        "HardResourceLimits": {"NumberOfFiles": 1024},
        "SoftResourceLimits": {"NumberOfFiles": 1024},
    },

    # ── Xcode Scheme (.xcscheme) ────────────────────────────────
    "xcode_scheme": {
        "ArchiveAction": {
            "buildConfiguration": "Release",
            "revealArchiveInOrganizer": True,
        },
        "BuildAction": {
            "buildImplicitDependencies": True,
            "buildParallelEntries": True,
        },
        "LaunchAction": {
            "buildConfiguration": "Debug",
            "disableMainThreadChecker": False,
            "launchStyle": 0,
            "useCustomWorkingDirectory": False,
            "ignorePathExtensionSavePanel": False,
        },
        "ProfileAction": {
            "buildConfiguration": "Release",
            "shouldUseLaunchSchemeArgsEnv": True,
        },
        "RunAction": {
            "buildConfiguration": "Debug",
            "shouldUseLaunchSchemeArgsEnv": True,
            "savedToolIdentifier": "",
            "useCustomWorkingDirectory": False,
        },
        "TestAction": {
            "buildConfiguration": "Debug",
            "shouldUseLaunchSchemeArgsEnv": True,
            "codeCoverageEnabled": False,
        },
    },

    # ── Core Data Model ─────────────────────────────────────────
    "core_data_model": {
        "_XCCurrentVersionName": "Model.xcdatamodel",
        "current_version_id": "0",
    },

    # ── Network (ATS / App Transport Security) ──────────────────
    "ns_app_transport_security": {
        "NSAllowsArbitraryLoads": False,
        "NSAllowsLocalNetworking": True,
        "NSAllowsArbitraryLoadsForMedia": False,
        "NSAllowsArbitraryLoadsInWebContent": False,
        "NSExceptionDomains": {
            "example.com": {
                "NSExceptionAllowsInsecureHTTPLoads": False,
                "NSIncludesSubdomains": True,
                "NSExceptionRequiresForwardSecrecy": True,
                "NSExceptionMinimumTLSVersion": "TLSv1.2",
            }
        },
    },

    # ── Localization ────────────────────────────────────────────
    "localizations": {
        "CFBundleDevelopmentRegion": "zh_CN",
        "CFBundleLocalizations": ["zh_CN", "zh_TW", "en", "ja", "ko"],
        "CFBundleDisplayName": "应用名称",
    },

    # ── Test target ─────────────────────────────────────────────
    "test_target": {
        "TestTargetID": None,
        "TestSuite": {
            "TestCase": {
                "TestID": "",
                "TestName": "",
                "TestClassName": "",
                "TestMethodName": "",
            }
        }
    },

    # ── On Demand Resources ─────────────────────────────────────
    "on_demand_resources": {
        "IDSDistributedProvisioningProfileName": "",
        "ITSAppUsesNonExemptEncryption": False,
        "OnDemandResourcesEnabled": True,
    },

    # ── Xcode Project (.pbxproj) 片段 ──────────────────────────
    "pbxproj_comment": {
        "PBXResourcesBuildPhase": {
            "comment": "Resources",
            "files": [],
        },
        "PBXSourcesBuildPhase": {
            "comment": "Sources",
            "files": [],
        },
        "PBXFrameworksBuildPhase": {
            "comment": "Frameworks",
            "files": [],
        },
    },

}


# ─────────────────────────────────────────────
#  全局自动补全建议（key → 默认值）
# ─────────────────────────────────────────────
AUTO_FILL_SUGGESTIONS = {}
for tmpl in COMMON_STRUCTURES.values():
    if isinstance(tmpl, dict):
        AUTO_FILL_SUGGESTIONS.update(tmpl)


# ─────────────────────────────────────────────
#  PlistWriter — 核心序列化
# ─────────────────────────────────────────────
class PlistWriter:
    """将 Python 对象序列化到标准 Apple XML plist"""

    def __init__(self, indent: str = "  "):
        self.indent = indent

    def build(self, data) -> str:
        root = ET.Element("plist", version="1.0")
        self._append(root, data)
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty = dom.toprettyxml(indent=self.indent, encoding=None)
        lines = pretty.splitlines()
        if lines and lines[0].startswith("<?xml"):
            lines = lines[1:]
        lines = [l for l in lines if l.strip()]
        return "\n".join(lines)

    def _append(self, parent: ET.Element, value):
        if value is None:
            return
        vtype = type(value)
        if vtype is bool:
            ET.SubElement(parent, "true" if value else "false")
        elif vtype is int:
            child = ET.SubElement(parent, "integer")
            child.text = str(value)
        elif vtype is float:
            child = ET.SubElement(parent, "real")
            child.text = repr(value)
        elif vtype is str:
            child = ET.SubElement(parent, "string")
            child.text = value
        elif vtype is bytes:
            child = ET.SubElement(parent, "data")
            child.text = self._b64(value)
        elif vtype in (date, datetime):
            child = ET.SubElement(parent, "date")
            child.text = self._iso_date(value)
        elif vtype is list:
            child = ET.SubElement(parent, "array")
            for item in value:
                self._append(child, item)
        elif vtype is dict:
            child = ET.SubElement(parent, "dict")
            for key in value:
                kt = ET.SubElement(child, "key")
                kt.text = str(key)
                self._append(child, value[key])
        else:
            child = ET.SubElement(parent, "string")
            child.text = str(value)

    @staticmethod
    def _b64(data: bytes) -> str:
        import base64
        return base64.b64encode(data).decode()

    @staticmethod
    def _iso_date(dt) -> str:
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ─────────────────────────────────────────────
#  PlistBuilder — 交互式构建器
# ─────────────────────────────────────────────
class PlistBuilder:
    """
    交互式填写 plist，支持：
      • 自动从模板填充
      • 自动补全合法值
      • 类型自动推断
      • 嵌套结构路径访问
    """

    def __init__(self):
        self.data = {}
        self.writer = PlistWriter()
        self._history = []   # undo 栈

    # ── 基础操作 ───────────────────────────────────────

    def load_template(self, name: str):
        """加载内置模板"""
        if name not in COMMON_STRUCTURES:
            available = ", ".join(sorted(COMMON_STRUCTURES.keys()))
            raise ValueError(
                f"未知模板: {name}\n可用模板 ({len(COMMON_STRUCTURES)} 个)：\n  {available}"
            )
        self.data = copy.deepcopy(COMMON_STRUCTURES[name])
        print(f"✅ 已加载模板: {name}  ({len(self.data)} 个顶层键)")

    def set(self, key_path: str, value):
        """设置值，支持点分隔路径"""
        keys = key_path.split(".")
        target = self.data
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def get(self, key_path: str, default=None):
        """读取值"""
        keys = key_path.split(".")
        target = self.data
        try:
            for k in keys:
                target = target[k]
            return target
        except (KeyError, TypeError):
            return default

    def delete(self, key_path: str):
        """删除键"""
        keys = key_path.split(".")
        target = self.data
        try:
            for k in keys[:-1]:
                target = target[k]
            del target[keys[-1]]
        except (KeyError, TypeError):
            pass

    def append_array_item(self, key_path: str, value):
        """向数组追加元素"""
        arr = self.get(key_path)
        if arr is None:
            self.set(key_path, [value])
        elif isinstance(arr, list):
            arr.append(value)
        else:
            raise TypeError(f"{key_path} 不是数组，是 {type(arr).__name__}")

    def pretty_print(self):
        """打印当前结构"""
        print("\n📋 当前 plist 结构：")
        print(self.writer.build(self.data))
        print()

    # ── 自动补全 ───────────────────────────────────────

    def auto_fill(self, key: str, value=None):
        """根据常见 key 自动填充值"""
        if value is None:
            value = AUTO_FILL_SUGGESTIONS.get(key, "")
        return value

    def suggest(self, prefix: str = "") -> dict:
        """根据前缀返回可用的 key 建议"""
        if prefix:
            return {k: AUTO_FILL_SUGGESTIONS[k]
                    for k in sorted(AUTO_FILL_SUGGESTIONS)
                    if k.startswith(prefix)}
        return dict(sorted(AUTO_FILL_SUGGESTIONS.items()))

    def search_key(self, keyword: str) -> list:
        """模糊搜索包含关键词的 key"""
        kw = keyword.lower()
        return [(k, AUTO_FILL_SUGGESTIONS[k])
                for k in sorted(AUTO_FILL_SUGGESTIONS)
                if kw in k.lower()]

    # ── 输出 ───────────────────────────────────────────

    def save(self, path: str = "output.plist"):
        """保存为 XML plist 文件"""
        content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        content += self.writer.build(self.data)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"💾 已保存: {path}")
        return path

    def to_string(self) -> str:
        """返回 XML 字符串"""
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + self.writer.build(self.data)


# ─────────────────────────────────────────────
#  类型解析
# ─────────────────────────────────────────────
def parse_value(s: str):
    """从字符串自动推断 plist 合法类型"""
    s = s.strip()
    if s.lower() in ("true", "yes", "1"):
        return True
    if s.lower() in ("false", "no", "0"):
        return False
    if s.lower() in ("null", "none"):
        return None
    if s.isdigit():
        return int(s)
    try:
        return float(s)
    except ValueError:
        pass
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [parse_value(x.strip()) for x in inner.split(",")]
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        if not inner:
            return {}
        result = {}
        for pair in inner.split(","):
            if ":" not in pair:
                continue
            k, v = pair.split(":", 1)
            result[k.strip()] = parse_value(v.strip())
        return result
    return s


# ─────────────────────────────────────────────
#  交互式 CLI
# ─────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════
#  交互式 CLI（TUI 模式 + 行模式 + 非交互批处理）
# ═══════════════════════════════════════════════════════════════


class TUI:
    """
    基于 curses + rich 的全屏 TUI 界面。
    三栏布局：左侧模板列表 | 中间结构树 | 底部命令/编辑区
    """

    TEMPLATE_CATEGORIES = {
        "Info.plist": [k for k in COMMON_STRUCTURES if k.startswith("info_")],
        "Entitlements": [k for k in COMMON_STRUCTURES if k.startswith("entitlements")],
        "Xcode": [k for k in COMMON_STRUCTURES if k in (
            "build_settings", "scene_config", "xcode_scheme", "pbxproj_comment")],
        "App Services": [k for k in COMMON_STRUCTURES if k in (
            "itunes_sandbox", "itunes_metadata", "storekit_external_purchase",
            "gamecenter_sandbox")],
        "Assets & Data": [k for k in COMMON_STRUCTURES if k in (
            "asset_catalog", "swift_resolved", "user_defaults", "user_activity")],
        "System": [k for k in COMMON_STRUCTURES if k in (
            "launchd", "core_data_model", "ns_app_transport_security",
            "localizations", "test_target", "on_demand_resources")],
    }

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.builder = PlistBuilder()
        self.current_template = None
        self.selected_template_idx = 0
        self.category_idx = 0
        self.item_idx = 0
        self.message = ""
        self.edit_mode = False
        self.edit_key = ""
        self.edit_value = ""
        self.edit_cursor = 0
        self.view = "templates"   # templates | structure | help
        self.max_y = 0
        self.max_x = 0
        self.scroll_top = 0
        self.scroll_left = 0

    # ── 运行 ───────────────────────────────────────────────────

    def run(self):
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        except Exception:
            pass

        self.max_y, self.max_x = self.stdscr.getmaxyx()

        while True:
            self.max_y, self.max_x = self.stdscr.getmaxyx()
            self._draw()
            key = self.stdscr.getch()
            self._handle_key(key)
            if not self.running:
                break

    @property
    def running(self):
        return True

    # ── 绘制 ───────────────────────────────────────────────────

    def _draw(self):
        self.stdscr.clear()
        h, w = self.max_y, self.max_x

        # 标题栏
        self._attr(0, 0, w, curses.A_REVERSE | curses.A_BOLD)
        self.stdscr.addstr(0, 2, " 🍎 Apple Plist Writer TUI ", curses.A_REVERSE | curses.A_BOLD)
        mode_label = "[EDIT]" if self.edit_mode else f"[MODE: {self.view.upper()}]"
        self.stdscr.addstr(0, w - len(mode_label) - 1, mode_label, curses.A_REVERSE)

        if self.view == "templates":
            self._draw_templates(h, w)
        elif self.view == "structure":
            self._draw_structure(h, w)
        elif self.view == "help":
            self._draw_help(h, w)

        # 底部状态栏
        self._attr(h - 3, 0, w, curses.A_REVERSE)
        self.stdscr.addstr(h - 3, 2, f" Template: {self.current_template or '— 未加载 —':<30} ", curses.A_REVERSE)

        if self.edit_mode:
            self._attr(h - 2, 0, w, curses.color_pair(1))
            prompt = f" Key: {self.edit_key}"
            self.stdscr.addstr(h - 2, 2, prompt)
            val_display = f"Value: {self.edit_value[:w-len(prompt)-4]}"
            self.stdscr.addstr(h - 2, 2 + len(prompt), val_display)
            curses.curs_set(1)
        else:
            curses.curs_set(0)
            self._attr(h - 2, 0, w, curses.A_DIM)
            shortcuts = " ↑↓/Tab:导航  Enter:选择  e:编辑  a:追加  d:删除  s:保存  q:退出 "
            self.stdscr.addstr(h - 2, 2, shortcuts[:w - 4])

        if self.message:
            self._attr(h - 1, 0, w, curses.A_BOLD | curses.color_pair(2))
            self.stdscr.addstr(h - 1, 2, self.message[:w - 4])
            self.message = ""

        self.stdscr.refresh()

    def _draw_templates(self, h, w):
        """三栏：分类 | 模板列表 | 预览"""
        col_w = [22, 26, w - 50]
        col_x = [0, col_w[0], col_w[0] + col_w[1]]

        # 分类列
        cats = list(self.TEMPLATE_CATEGORIES.keys())
        for i, cat in enumerate(cats):
            attr = curses.A_REVERSE if i == self.category_idx else curses.A_NORMAL
            self._attr(1 + i, col_x[0], col_w[0], attr)
            self.stdscr.addstr(1 + i, col_x[0] + 2, cat[:col_w[0] - 2])

        # 模板列表列
        items = self.TEMPLATE_CATEGORIES[cats[self.category_idx]]
        list_h = h - 4
        for i in range(min(list_h, len(items))):
            real_idx = self.scroll_top + i
            if real_idx >= len(items):
                break
            name = items[real_idx]
            data = COMMON_STRUCTURES[name]
            sample = list(data.keys())[:2]
            attr = (curses.A_REVERSE | curses.A_BOLD if real_idx == self.item_idx
                    else curses.A_NORMAL)
            self._attr(1 + i, col_x[1], col_w[1], attr)
            self.stdscr.addstr(1 + i, col_x[1] + 2, name[:col_w[1] - 3])

        # 预览列
        if 0 <= self.item_idx < len(items):
            tname = items[self.item_idx]
            preview = COMMON_STRUCTURES[tname]
            self._attr(1, col_x[2], col_w[2], curses.A_BOLD)
            self.stdscr.addstr(1, col_x[2] + 2, f"模板: {tname}  ({len(preview)} keys)")
            row = 2
            for key in list(preview.keys())[:list_h - 4]:
                if row >= h - 3:
                    break
                self._attr(row, col_x[2], col_w[2], curses.A_DIM)
                v = preview[key]
                vstr = repr(v) if not isinstance(v, (dict, list)) else type(v).__name__
                line = f"  {key}: {vstr}"
                self.stdscr.addstr(row, col_x[2] + 1, line[:col_w[2] - 2])
                row += 1

        # 分隔线
        for x in [col_w[0], col_w[0] + col_w[1]]:
            for y in range(1, h - 3):
                try:
                    self.stdscr.addstr(y, x, "│")
                except Exception:
                    pass

    def _draw_structure(self, h, w):
        """显示当前 builder.data 的树形结构"""
        if not self.builder.data:
            self._attr(2, 2, w, curses.A_DIM)
            self.stdscr.addstr(2, 2, "（未加载模板，请先在 Templates 视图中加载）")
            return
        lines = self._build_tree(self.builder.data, indent=0)
        for i, (indent, key, val, is_last) in enumerate(lines):
            if i >= h - 4:
                break
            line = "  " * indent + ("└─ " if is_last else "├─ ") + key
            if val is not None:
                line += f": {repr(val) if len(repr(val)) < 40 else repr(val)[:37]+'...'}"
            self._attr(1 + i, 0, w, curses.A_NORMAL)
            self.stdscr.addstr(1 + i, 1, line[:w - 2])

    def _draw_help(self, h, w):
        lines = HELP_TUI.splitlines()
        for i, line in enumerate(lines[:h - 4]):
            self._attr(1 + i, 0, w, curses.A_NORMAL)
            self.stdscr.addstr(1 + i, 2, line[:w - 4])

    def _build_tree(self, data, indent=0, parent_is_last=False):
        lines = []
        if not isinstance(data, dict):
            return [(indent, "(value)", data, True)]
        items = list(data.items())
        for idx, (key, val) in enumerate(items):
            is_last = (idx == len(items) - 1)
            lines.append((indent, str(key), val, is_last))
            if isinstance(val, dict):
                lines += self._build_tree(val, indent + 1, is_last)
            elif isinstance(val, list):
                lines.append((indent + 1, f"[array ×{len(val)}]", None, True))
                for li, lv in enumerate(val[:3]):
                    lines.append((indent + 2, f"[{li}]", lv, li == min(2, len(val) - 1)))
                if len(val) > 3:
                    lines.append((indent + 2, f"... ({len(val)-3} more)", None, True))
        return lines

    # ── 键盘处理 ───────────────────────────────────────────────

    def _handle_key(self, key):
        if self.edit_mode:
            self._handle_edit(key)
            return

        cats = list(self.TEMPLATE_CATEGORIES.keys())
        items = self.TEMPLATE_CATEGORIES[cats[self.category_idx]]

        if key in (curses.KEY_UP, ord("k")):
            self.item_idx = max(0, self.item_idx - 1)
            self.scroll_top = min(self.scroll_top, self.item_idx)
        elif key in (curses.KEY_DOWN, ord("j")):
            self.item_idx = min(len(items) - 1, self.item_idx + 1)
            list_h = self.max_y - 4
            if self.item_idx >= self.scroll_top + list_h:
                self.scroll_top = self.item_idx - list_h + 1
        elif key in (curses.KEY_LEFT, curses.KEY_BTAB):
            self.category_idx = (self.category_idx - 1) % len(cats)
            self.item_idx = 0
            self.scroll_top = 0
        elif key in (curses.KEY_RIGHT, ord("\t")):
            self.category_idx = (self.category_idx + 1) % len(cats)
            self.item_idx = 0
            self.scroll_top = 0
        elif key in (curses.KEY_ENTER, ord("\n"), ord("l")):
            if items and 0 <= self.item_idx < len(items):
                tname = items[self.item_idx]
                try:
                    self.builder.load_template(tname)
                    self.current_template = tname
                    self.view = "structure"
                    self.message = f"✅ 已加载: {tname}"
                except Exception as e:
                    self.message = f"⚠️  {e}"
        elif key == ord("e"):
            if self.builder.data:
                self._start_edit()
        elif key == ord("a"):
            if self.builder.data:
                self._start_append()
        elif key == ord("d"):
            if self.builder.data:
                self._start_delete()
        elif key == ord("s"):
            self._save()
        elif key == ord("w"):
            self.view = "structure"
        elif key == ord("t"):
            self.view = "templates"
        elif key == ord("?") or key == ord("h"):
            self.view = "help"
        elif key == ord("q") or key == 27:
            self.running = False

    def _start_edit(self):
        self.edit_mode = True
        self.edit_key = ""
        self.edit_value = ""
        self.edit_is_append = False

    def _start_append(self):
        self.edit_mode = True
        self.edit_key = ""
        self.edit_value = ""
        self.edit_is_append = True

    def _start_delete(self):
        self.edit_key = ""
        self.edit_value = ""
        self.message = "📝 输入要删除的 key（或 q 取消），按 Enter 确认"

        # 简易：弹一个 mini 输入框
        curses.echo()
        curses.curs_set(1)
        try:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            self.stdscr.addstr(h // 2 - 1, 2, "删除 key（或 q 取消）: ")
            val = self.stdscr.getstr(h // 2, 2, w - 4).decode()
            if val and val != "q":
                self.builder.delete(val)
                self.message = f"✅ 已删除: {val}"
            else:
                self.message = "已取消"
        finally:
            curses.noecho()
            curses.curs_set(0)

    def _save(self):
        if not self.builder.data:
            self.message = "⚠️  没有可保存的数据"
            return
        curses.echo()
        curses.curs_set(1)
        try:
            h, w = self.stdscr.getmaxyx()
            self.stdscr.clear()
            self.stdscr.addstr(h // 2 - 1, 2, "保存路径（默认 output.plist）: ")
            path = self.stdscr.getstr(h // 2, 2, w - 4).decode().strip()
            if not path:
                path = "output.plist"
            self.builder.save(path)
            self.message = f"💾 已保存: {path}"
        finally:
            curses.noecho()
            curses.curs_set(0)

    def _handle_edit(self, key):
        if key in (curses.KEY_ENTER, ord("\n")):
            self._commit_edit()
        elif key == curses.KEY_BACKSPACE or key in (127, 8):
            if self.edit_value:
                self.edit_value = self.edit_value[:-1]
            elif self.edit_key:
                self.edit_key = self.edit_key[:-1]
        elif key == 27:  # ESC — 取消
            self.edit_mode = False
            self.message = "已取消"
        elif 32 <= key <= 126:
            ch = chr(key)
            if self.edit_key == "":
                self.edit_key += ch
            else:
                self.edit_value += ch

    def _commit_edit(self):
        if not self.edit_key:
            self.edit_mode = False
            self.message = "已取消"
            return
        try:
            value = parse_value(self.edit_value) if self.edit_value else ""
            if getattr(self, 'edit_is_append', False):
                self.builder.append_array_item(self.edit_key, value)
                self.message = f"✅ append → {self.edit_key} = {repr(value)}"
            else:
                self.builder.set(self.edit_key, value)
                self.message = f"✅ set {self.edit_key} = {repr(value)}"
        except Exception as e:
            self.message = f"⚠️  {e}"
        self.edit_mode = False

    # ── 辅助 ───────────────────────────────────────────────────

    def _attr(self, y, x, w, attr):
        """在指定区域应用属性（背景色清除）"""
        try:
            self.stdscr.addstr(y, x, " " * min(w, self.max_x - x), attr)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
#  行模式 CLI（原始交互式终端）
# ═══════════════════════════════════════════════════════════════

def run_cli():
    """纯行输入 CLI，无需 ncurses，适合 SSH / 远程"""
    import shutil
    cols = shutil.get_terminal_size().columns
    print("=" * min(cols, 56))
    print("  🍎 Apple XML Property List 自动编写工具 v3")
    print("=" * min(cols, 56))
    print()
    print("可用模板：")
    for i, name in enumerate(sorted(COMMON_STRUCTURES.keys()), 1):
        sample = list(COMMON_STRUCTURES[name].keys())[:2]
        print(f"  {i:>2}. {name:<30} {', '.join(sample)}")
    print()

    builder = PlistBuilder()

    while True:
        try:
            cmd = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break
        if not cmd:
            continue

        parts = cmd.split(None, 1)
        verb = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        try:
            if verb in ("q", "quit", "exit"):
                print("👋 再见！")
                break

            elif verb == "load":
                builder.load_template(arg)
                builder.pretty_print()

            elif verb == "set":
                if "=" not in arg:
                    print("❌ 格式: set key=value 或 set path.to.key=value")
                    continue
                k, v = arg.split("=", 1)
                builder.set(k, parse_value(v))
                print(f"✅ set {k} = {repr(parse_value(v))}")

            elif verb == "append":
                if "=" not in arg:
                    print("❌ 格式: append arrayKey=value")
                    continue
                k, v = arg.split("=", 1)
                builder.append_array_item(k, parse_value(v))
                print(f"✅ append → {k}: {repr(parse_value(v))}")

            elif verb == "delete":
                builder.delete(arg)
                print(f"✅ deleted: {arg}")

            elif verb == "get":
                val = builder.get(arg)
                print(f"  {arg} = {repr(val)}")

            elif verb == "search":
                results = builder.search_key(arg)
                if results:
                    print(f"🔍 找到 {len(results)} 个：")
                    for k, v in results:
                        print(f"  {k}: {repr(v)}")
                else:
                    print("🔍 无匹配")

            elif verb == "autofill":
                for k, v in builder.suggest(arg).items():
                    print(f"  {k}: {repr(v)}")

            elif verb == "list":
                builder.pretty_print()

            elif verb == "save":
                builder.save(arg or "output.plist")

            elif verb == "show":
                print(builder.to_string())

            elif verb == "templates":
                for name in sorted(COMMON_STRUCTURES):
                    print(f"  • {name} ({len(COMMON_STRUCTURES[name])} keys)")

            elif verb == "help":
                print(HELP_TEXT)

            elif verb == "tui":
                print("🔄 切换到 TUI 模式...")
                curses.wrapper(lambda s: TUI(s).run())

            else:
                print(f"❓ 未知命令: {verb}，输入 help 查看帮助")

        except Exception as e:
            print(f"⚠️  错误: {e}")


# ═══════════════════════════════════════════════════════════════
#  非交互批处理（适合脚本调用）
# ═══════════════════════════════════════════════════════════════

def run_batch(args):
    """一行命令完成：加载模板 → 设值 → 保存，无需交互"""
    builder = PlistBuilder()

    if args.template:
        builder.load_template(args.template)

    for op in (args.set or []):
        if "=" in op:
            k, v = op.split("=", 1)
            builder.set(k, parse_value(v))
    for op in (args.append or []):
        if "=" in op:
            k, v = op.split("=", 1)
            builder.append_array_item(k, parse_value(v))
    for key in (args.delete or []):
        builder.delete(key)

    if args.out:
        builder.save(args.out)
    elif args.show:
        print(builder.to_string())
    else:
        print(builder.to_string())


HELP_TUI = """\
┌─────────────────────────────────────────────────┐
│  Apple Plist Writer — TUI 操作说明               │
├─────────────────────────────────────────────────┤
│  ↑↓        选择模板 / 浏览结构                  │
│  ←→ Tab    切换 分类列表 / 模板列表 / 预览       │
│  Enter/l   加载选中的模板并进入 Structure 视图   │
│  e         编辑键值（set key=value）            │
│  a         向数组追加（append key=value）        │
│  d         删除键                                │
│  s         保存到文件                            │
│  t         返回 Templates 视图                   │
│  w         进入 Structure 视图                   │
│  h / ?     显示帮助                              │
│  q / Esc   退出                                  │
├─────────────────────────────────────────────────┤
│  命令行模式输入  python3 plist_writer.py --cli  │
│  批处理模式     python3 plist_writer.py -t info_ios \
│                   --set CFBundleIdentifier=com.example \
│                   --save out.plist               │
└─────────────────────────────────────────────────┘"""


HELP_TEXT = """
🍎 命令说明：

  load <模板名>       加载内置模板（见 templates）
  set   key=value    设置键值（点路径自动创建嵌套）
  append key=value   向数组追加元素
  delete key         删除键
  get   key          读取键值
  search <关键词>     模糊搜索包含关键词的合法 key
  autofill [前缀]    列出自动补全建议
  list               打印当前完整结构
  save  [文件名]     保存为 .plist（默认 output.plist）
  show               输出 XML 文本
  templates          列出所有内置模板
  help               显示本帮助
  q                  退出

📌 快捷输入格式：
  set CFBundleIdentifier=com.example.app
  set UIApplicationSceneManifest.UIApplicationSupportsMultipleScenes=true
  append UISupportedInterfaceOrientations=UIInterfaceOrientationLandscapeLeft
  set UIApplicationShortcutItems=[{{"UIApplicationShortcutItemType":"com.example.action","UIApplicationShortcutItemTitle":"Action"}}]

💡 自动类型推断：
  true/false      → bool
  123 / 3.14      → integer / real
  [...]           → array
  DICT_FMT         → dict（见上方 set 命令示例）
  null            → None（不写入）
  其他            → string

📦 当前模板列表（共 {n} 个）：
  info_ios          iOS / iPadOS Info.plist（含隐私描述键）
  info_macos        macOS Info.plist
  info_watchos      watchOS App Info.plist
  info_watchkit_app watchOS Glance / WatchKit App
  info_widget       Widget Extension
  info_notification_ext  Notification Service Extension
  info_share_ext    Share Extension
  info_photo_edit_ext   Photo Editing Extension
  info_appclip      App Clip
  info_safari_ext   Safari Web Extension
  info_intent_ext   Intent Extension (SiriKit)
  entitlements      .entitlements（通用沙盒）
  entitlements_icloud   iCloud entitlements
  entitlements_push     Push Notification entitlements
  entitlements_app_groups  App Groups + Keychain
  entitlements_mac   macOS entitlements
  entitlements_tvos  tvOS entitlements
  build_settings    Xcode Build Settings
  scene_config      UIWindowScene 配置
  asset_catalog     Asset Catalog Contents.json
  swift_resolved    Swift Package Resolved
  user_defaults     UserDefaults 种子数据
  user_activity     NSUserActivity
  launchd           launchd daemon/agent plist
  xcode_scheme      Xcode Scheme
  core_data_model   Core Data Model
  ns_app_transport_security  ATS 网络安全配置
  localizations     本地化配置
  test_target       Test target 片段
  on_demand_resources  On Demand Resources
  pbxproj_comment   Xcode Project 片段
  itunes_sandbox    iTunes Sandbox 配置
  itunes_metadata   App Store iTunesMetadata.plist
  storekit_external_purchase  StoreKit 第三方支付沙盒
  gamecenter_sandbox  Game Center Sandbox
""".format(n=len(COMMON_STRUCTURES))


# ═══════════════════════════════════════════════════════════════
#  GitHub CLI 风格输出函数
# ═══════════════════════════════════════════════════════════════

class GitStyleOutput:
    """GitHub CLI 风格的格式化输出"""
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[31m"
    GREEN  = "\033[32m"
    YELLOW = "\033[33m"
    BLUE   = "\033[34m"
    CYAN   = "\033[36m"

    @classmethod
    def error(cls, msg):   return f"{cls.RED}error{cls.RESET}: {msg}"
    @classmethod
    def warning(cls, msg): return f"{cls.YELLOW}warning{cls.RESET}: {msg}"
    @classmethod
    def success(cls, msg): return f"{cls.GREEN}✓ {cls.RESET}{msg}"
    @classmethod
    def info(cls, msg):    return f"{cls.BLUE}info{cls.RESET}: {msg}"
    @classmethod
    def header(cls, msg):  return f"\n{cls.BOLD}{msg}{cls.RESET}\n"

    @staticmethod
    def section(title):
        print(f"\n{GitStyleOutput.BOLD}{title}{GitStyleOutput.RESET}")

    @staticmethod
    def key_val(key, val, indent=2):
        print(f"{' '*indent}{GitStyleOutput.CYAN}{key}{GitStyleOutput.RESET}  {val}")

    @staticmethod
    def dim(msg):
        print(f"{GitStyleOutput.DIM}{msg}{GitStyleOutput.RESET}")

    @staticmethod
    def bold(msg):
        print(f"{GitStyleOutput.BOLD}{msg}{GitStyleOutput.RESET}")


# ═══════════════════════════════════════════════════════════════
#  argparse 主入口 — GitHub CLI 风格
# ═══════════════════════════════════════════════════════════════

def build_argparser():
    p = argparse.ArgumentParser(
        prog="plist",
        description="Apple XML Property List 自动编写工具。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE
  plist <command> [<flags>]

AVAILABLE COMMANDS
  init            交互式创建 plist，引导选择模板并填充内容
  set             设置键值，支持点路径自动创建嵌套结构
  get             读取键值，支持点路径批量读取
  delete          删除键
  append          向数组追加元素
  list            列出当前 plist 完整结构
  save            保存为 .plist 文件
  show            输出 XML 内容到标准输出
  templates       列出所有可用模板

EXAMPLES
  # 交互式初始化
  plist init
  plist init -t info_ios

  # 设置值（点路径自动创建嵌套）
  plist set CFBundleIdentifier=com.example.app
  plist set UIApplicationSceneManifest.UIApplicationSupportsMultipleScenes=true
  plist set UIBackgroundModes=[audio,fetch,remote-notification]
  plist set NSAppTransportSecurity.NSExceptionDomains.api.example.com.NSIncludesSubdomains=true

  # 读取值
  plist get CFBundleIdentifier
  plist get UIApplicationSceneManifest

  # 删除、追加、保存
  plist delete UILaunchStoryboardName
  plist append UISupportedInterfaceOrientations UIInterfaceOrientationLandscapeLeft
  plist save Info.plist
  plist show

  # 一行批处理（无需交互）
  plist init -t info_ios \
    --set CFBundleIdentifier=com.mycompany.myapp \
    --set CFBundleDisplayName=我的应用 \
    --set UIApplicationSceneManifest.UIApplicationSupportsMultipleScenes=true \
    --save Info.plist

LEARN MORE
  plist init --help
  plist set --help
  plist templates --help
""",
    )
    p.add_argument("--tui", action="store_true",
                   help="启动全屏 TUI 界面（curses-based）")

    sub = p.add_subparsers(dest="command", title="commands", metavar="")

    # ── plist init ──────────────────────────────────────────────
    p_init = sub.add_parser("init", help="创建并初始化一个 plist 文件",
                            description="加载模板后进入交互式编辑，或通过 flags 一次性完成设值并保存。")
    p_init.add_argument("-t", "--template", metavar="TEMPLATE",
                        help="初始化的模板名（必选）")
    p_init.add_argument("--set", action="append", dest="set", metavar="KEY=VALUE",
                        help="设值（可多次）")
    p_init.add_argument("--append", action="append", dest="append", metavar="KEY=VALUE",
                        help="向数组追加元素（可多次）")
    p_init.add_argument("--delete", action="append", dest="delete", metavar="KEY",
                        help="删除键（可多次）")
    p_init.add_argument("-s", "--save", "--output", dest="save", metavar="FILE",
                        help="初始化完成后直接保存到文件")
    p_init.add_argument("--no-interact", action="store_true",
                        help="非交互模式：使用 --set/--append/--delete 完成所有操作后退出")

    # ── plist set ───────────────────────────────────────────────
    p_set = sub.add_parser("set", help="设置键值",
                           description="支持点路径自动创建嵌套结构。类型根据 VALUE 自动推断。")
    p_set.add_argument("kv", metavar="KEY=VALUE",
                       help="键值对，格式为 KEY=VALUE，支持点路径，如 CFBundleIdentifier=com.example")
    p_set.add_argument("-t", "--template", metavar="TEMPLATE",
                       help="使用指定模板作为当前上下文（不指定则新建空白 plist）")
    p_set.add_argument("--save", metavar="FILE",
                       help="设置后保存到文件")
    p_set.add_argument("--show", action="store_true",
                       help="设置后输出完整 XML 到标准输出")

    # ── plist get ───────────────────────────────────────────────
    p_get = sub.add_parser("get", help="读取键值",
                           description="读取指定 key 的值；不指定 key 则列出所有顶层键。")
    p_get.add_argument("key", nargs="?", metavar="KEY",
                       help="要读取的 key（支持点路径）；省略则列出所有顶层键")
    p_get.add_argument("-t", "--template", metavar="TEMPLATE",
                       help="从指定模板读取（不指定则使用当前内存中的 plist）")
    p_get.add_argument("-j", "--json", action="store_true",
                       help="以 JSON 格式输出值（适用于复杂结构）")

    # ── plist delete ────────────────────────────────────────────
    p_del = sub.add_parser("delete", help="删除键",
                           description="从当前 plist 中删除指定 key。")
    p_del.add_argument("key", metavar="KEY",
                       help="要删除的 key（支持点路径）")
    p_del.add_argument("-t", "--template", metavar="TEMPLATE",
                       help="从指定模板删除（不指定则使用当前内存中的 plist）")
    p_del.add_argument("--save", metavar="FILE",
                       help="删除后保存到文件")
    p_del.add_argument("--show", action="store_true",
                       help="删除后输出完整 XML")

    # ── plist append ────────────────────────────────────────────
    p_app = sub.add_parser("append", help="向数组追加元素",
                           description="将 VALUE 追加到 KEY 对应的数组中；若 key 不存在则自动创建数组。")
    p_app.add_argument("key", metavar="KEY",
                       help="目标数组的 key（支持点路径）")
    p_app.add_argument("value", metavar="VALUE",
                       help="要追加的值，类型自动推断")
    p_app.add_argument("-t", "--template", metavar="TEMPLATE",
                       help="使用指定模板")
    p_app.add_argument("--save", metavar="FILE",
                       help="追加后保存到文件")
    p_app.add_argument("--show", action="store_true",
                       help="追加后输出完整 XML")

    # ── plist list ──────────────────────────────────────────────
    p_list = sub.add_parser("list", help="列出结构",
                            description="以树形结构显示当前 plist 内容。")
    p_list.add_argument("-t", "--template", metavar="TEMPLATE",
                        help="列出指定模板的结构")
    p_list.add_argument("-j", "--json", action="store_true",
                        help="以 JSON 格式输出（用于程序化处理）")

    # ── plist save ──────────────────────────────────────────────
    p_save = sub.add_parser("save", help="保存 plist",
                            description="将当前 plist 保存到文件。")
    p_save.add_argument("file", nargs="?", default="output.plist", metavar="FILE",
                        help="保存路径（默认 output.plist）")
    p_save.add_argument("-t", "--template", metavar="TEMPLATE",
                        help="将指定模板保存到文件")
    p_save.add_argument("--overwrite", action="store_true",
                        help="覆盖已存在的文件（默认不覆盖）")

    # ── plist show ──────────────────────────────────────────────
    p_show = sub.add_parser("show", help="输出 XML 内容",
                            description="将当前 plist 输出为标准 Apple XML plist 格式。")
    p_show.add_argument("-t", "--template", metavar="TEMPLATE",
                        help="输出指定模板的 XML 内容")
    p_show.add_argument("--color", choices=["always", "auto", "never"], default="auto",
                        help="是否对 XML 语法着色（默认 auto）")

    # ── plist templates ─────────────────────────────────────────
    p_tpl = sub.add_parser("templates", help="列出所有模板",
                           description=f"列出全部 {len(COMMON_STRUCTURES)} 个可用模板。")
    p_tpl.add_argument("-c", "--category", metavar="CATEGORY",
                       help="只列出指定分类的模板（Info.plist / Entitlements / Xcode / App Services / Assets & Data / System）")
    p_tpl.add_argument("-s", "--search", metavar="PATTERN",
                       help="搜索名称包含 PATTERN 的模板")
    p_tpl.add_argument("-j", "--json", action="store_true",
                       help="以 JSON 格式输出")

    return p


# ═══════════════════════════════════════════════════════════════
#  命令处理器 — 对应每个 subcommand
# ═══════════════════════════════════════════════════════════════

def cmd_init(args, builder: PlistBuilder):
    if args.template:
        builder.load_template(args.template)
        GitStyleOutput.success(f"Loaded template: {args.template}")
    else:
        GitStyleOutput.info("No template specified, starting from empty plist. Use --template to select one.")

    for op in (args.set or []):
        if "=" not in op:
            print(GitStyleOutput.error(f"Invalid format: {op} (expected KEY=VALUE)"))
            continue
        k, v = op.split("=", 1)
        builder.set(k, parse_value(v))
        print(GitStyleOutput.success(f"set {k} = {repr(parse_value(v))}"))

    for op in (args.append or []):
        if "=" not in op:
            print(GitStyleOutput.error(f"Invalid format: {op}")); continue
        k, v = op.split("=", 1)
        builder.append_array_item(k, parse_value(v))
        print(GitStyleOutput.success(f"append {k} = {repr(parse_value(v))}"))

    for key in (args.delete or []):
        builder.delete(key)
        print(GitStyleOutput.success(f"deleted: {key}"))

    if args.save:
        builder.save(args.save)
        print(GitStyleOutput.success(f"Saved to {args.save}"))

    if not args.no_interact:
        run_cli()   # 降级到行模式继续交互


def cmd_set(args, builder: PlistBuilder):
    if "=" not in args.kv:
        print(GitStyleOutput.error(f"Expected KEY=VALUE, got: {args.kv}"))
        return
    k, v = args.kv.split("=", 1)
    val = parse_value(v)
    builder.set(k, val)
    print(GitStyleOutput.success(f"{k} = {repr(val)}"))
    _maybe_output(builder, args.save, args.show)


def cmd_get(args, builder: PlistBuilder):
    if args.key:
        val = builder.get(args.key)
        if val is None:
            print(GitStyleOutput.error(f"Key not found: {args.key}"))
        elif args.json:
            import json; print(json.dumps(val, ensure_ascii=False, indent=2))
        else:
            print(f"{GitStyleOutput.CYAN}{args.key}{GitStyleOutput.RESET}  {repr(val)}")
    else:
        GitStyleOutput.section("Top-level keys")
        for i, k in enumerate(sorted(builder.data.keys()), 1):
            v = builder.data[k]
            tag = type(v).__name__
            print(f"  {i:>2}. {GitStyleOutput.CYAN}{k}{GitStyleOutput.RESET}  ({tag})")


def cmd_delete(args, builder: PlistBuilder):
    if args.key not in builder.data and builder.get(args.key) is None:
        # 尝试路径
        pass
    builder.delete(args.key)
    print(GitStyleOutput.success(f"Deleted: {args.key}"))
    _maybe_output(builder, args.save, args.show)


def cmd_append(args, builder: PlistBuilder):
    val = parse_value(args.value)
    builder.append_array_item(args.key, val)
    print(GitStyleOutput.success(f"append {args.key} = {repr(val)}"))
    _maybe_output(builder, args.save, args.show)


def cmd_list(args, builder: PlistBuilder):
    if args.json:
        import json; print(json.dumps(builder.data, ensure_ascii=False, indent=2)); return
    if not builder.data:
        print(GitStyleOutput.warning("No plist loaded. Use 'plist init -t <template>' to load one."))
        return
    GitStyleOutput.section("Plist structure")
    lines = _build_tree_lines(builder.data)
    for line in lines[:200]:
        print(line)
    if len(lines) > 200:
        print(GitStyleOutput.dim(f"  ... ({len(lines)-200} more lines, use --json for full output)"))


def cmd_save(args, builder: PlistBuilder):
    import os as _os
    if _os.path.exists(args.file) and not args.overwrite:
        print(GitStyleOutput.error(f"File already exists: {args.file} (use --overwrite to replace)"))
        return
    builder.save(args.file)
    print(GitStyleOutput.success(f"Saved: {args.file}"))


def cmd_show(args, builder: PlistBuilder):
    xml = builder.to_string()
    if args.color == "always" or (args.color == "auto" and sys.stdout.isatty()):
        xml = _colorize_xml(xml)
    print(xml)


def cmd_templates(args, builder: PlistBuilder):
    import json
    templates = dict(sorted(COMMON_STRUCTURES.items()))

    if args.search:
        pat = args.search.lower()
        templates = {k: v for k, v in templates.items() if pat in k.lower()}
        if not templates:
            print(GitStyleOutput.warning(f"No templates matching: {args.search}"))
            return

    if args.category:
        cat_map = {
            "info.plist": "info_", "entitlements": "entitlements",
            "xcode": "build_settings",
            "app services": "itunes_sandbox",
            "assets & data": "asset_catalog",
            "system": "launchd",
        }
        prefix = cat_map.get(args.category.lower())
        if prefix:
            templates = {k: v for k, v in templates.items() if k.startswith(prefix)}

    if args.json:
        # 仅输出名称和 key 数量
        out = {k: {"keys": list(v.keys()), "key_count": len(v)} for k, v in templates.items()}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return

    GitStyleOutput.section(f"Available templates ({len(templates)})")
    for name in sorted(templates):
        keys = list(templates[name].keys())
        print(f"  {GitStyleOutput.CYAN}{name}{GitStyleOutput.RESET}")
        print(f"      {len(keys)} keys  |  {', '.join(keys[:3])}{' ...' if len(keys)>3 else ''}")


# ═══════════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════════

def _maybe_output(builder: PlistBuilder, save_path: str, show: bool):
    if save_path:
        builder.save(save_path)
        print(GitStyleOutput.success(f"Saved: {save_path}"))
    if show:
        print(builder.to_string())


def _build_tree_lines(data, indent=0, is_last=False):
    lines = []
    if not isinstance(data, dict):
        return ["  " * indent + f"└─ {repr(data)}"]
    items = list(data.items())
    prefix_fn = lambda last: "└─ " if last else "├─ "
    for idx, (key, val) in enumerate(items):
        last = (idx == len(items) - 1)
        if isinstance(val, dict):
            lines.append("  " * indent + f"├─ {GitStyleOutput.CYAN}{key}{GitStyleOutput.RESET}/")
            lines += _build_tree_lines(val, indent + 1, last)
        elif isinstance(val, list):
            lines.append("  " * indent + f"├─ {GitStyleOutput.CYAN}{key}{GitStyleOutput.RESET} [{len(val)} items]")
        else:
            vstr = repr(val)
            if len(vstr) > 60: vstr = vstr[:57] + "..."
            lines.append("  " * indent + f"{prefix_fn(last)}{GitStyleOutput.CYAN}{key}{GitStyleOutput.RESET}  {vstr}")
    return lines


def _colorize_xml(xml: str) -> str:
    """简单 XML 语法高亮（GitHub CLI 风格）"""
    c = GitStyleOutput
    out = []
    for line in xml.splitlines():
        if "<key>" in line:
            line = line.replace("<key>", f"{c.CYAN}<key>{c.RESET}")
            line = line.replace("</key>", f"{c.CYAN}</key>{c.RESET}")
        elif "<string>" in line:
            line = line.replace("<string>", f"{c.GREEN}<string>{c.RESET}")
            line = line.replace("</string>", f"{c.GREEN}</string>{c.RESET}")
        elif "<integer>" in line:
            line = line.replace("<integer>", f"{c.YELLOW}<integer>{c.RESET}")
            line = line.replace("</integer>", f"{c.YELLOW}</integer>{c.RESET}")
        elif "<true/>" in line:
            line = line.replace("<true/>", f"{c.GREEN}<true/>{c.RESET}")
        elif "<false/>" in line:
            line = line.replace("<false/>", f"{c.RED}<false/>{c.RESET}")
        elif "<real>" in line:
            line = line.replace("<real>", f"{c.YELLOW}<real>{c.RESET}")
            line = line.replace("</real>", f"{c.YELLOW}</real>{c.RESET}")
        elif "<date>" in line:
            line = line.replace("<date>", f"{c.BLUE}<date>{c.RESET}")
            line = line.replace("</date>", f"{c.BLUE}</date>{c.RESET}")
        elif "<dict>" in line:
            line = line.replace("<dict>", f"{c.BOLD}<dict>{c.RESET}")
            line = line.replace("</dict>", f"{c.BOLD}</dict>{c.RESET}")
        elif "<array>" in line:
            line = line.replace("<array>", f"{c.BOLD}<array>{c.RESET}")
            line = line.replace("</array>", f"{c.BOLD}</array>{c.RESET}")
        out.append(line)
    return "\n".join(out)


# ═══════════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = build_argparser()
    args = parser.parse_args()

    # 构建 builder 实例
    builder = PlistBuilder()
    tmpl = getattr(args, "template", None)
    if tmpl:
        builder.load_template(tmpl)

    # 无 command → 启动默认的文字用户界面
    if not args.command:
        if args.tui:
            curses.wrapper(lambda s: _tui_main(s, None))
        else:
            run_cli()
        sys.exit(0)

    # 有 command 时忽略 --tui（command 模式不支持 TUI）
    # （保留 builder 注入，后续可扩展）

    dispatch = {
        "init":       cmd_init,
        "set":        cmd_set,
        "get":        cmd_get,
        "delete":     cmd_delete,
        "append":     cmd_append,
        "list":       cmd_list,
        "save":       cmd_save,
        "show":       cmd_show,
        "templates":  cmd_templates,
    }
    handler = dispatch.get(args.command)
    if handler:
        handler(args, builder)
    else:
        print(GitStyleOutput.error(f"Unknown command: {args.command}"))
        parser.print_help()
        sys.exit(1)
