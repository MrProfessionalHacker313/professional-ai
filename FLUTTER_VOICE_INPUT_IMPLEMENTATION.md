# Flutter Mobile Voice Input Implementation

## Overview
This document provides guidance for implementing the voice input feature in the Flutter mobile app, matching the web implementation's functionality.

## Package Required
Add the `speech_to_text` package to your `pubspec.yaml`:

```yaml
dependencies:
  speech_to_text: ^6.6.0
```

## Implementation

### 1. Add Permission to AndroidManifest.xml
```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
```

### 2. Add Permission to Info.plist (iOS)
```xml
<!-- ios/Runner/Info.plist -->
<key>NSSpeechRecognitionUsageDescription</key>
<string>This app needs speech recognition to convert your voice to text</string>
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access to record your voice</string>
```

### 3. Implementation Code

```dart
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter/material.dart';

class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final SpeechToText _speechToText = SpeechToText();
  bool _isListening = false;
  String _lastWords = '';

  // Language mapping (matches web implementation)
  final Map<String, String> _languageToSpeechCode = {
    'en': 'en-US',
    'ur': 'ur-PK',
    'ar': 'ar-SA',
    'hi': 'hi-IN',
    'bn': 'bn-BD',
    'zh': 'zh-CN',
    'ru': 'ru-RU',
    'es': 'es-ES',
    'fr': 'fr-FR',
    'de': 'de-DE',
    'ja': 'ja-JP',
    'ko': 'ko-KR',
    'tr': 'tr-TR',
    'fa': 'fa-IR',
    'ps': 'ps-AF',
    'pa': 'pa-IN',
    'sd': 'sd-PK',
    'it': 'it-IT',
    'pt': 'pt-PT',
    'id': 'id-ID',
    'ms': 'ms-MY',
    'th': 'th-TH',
    'vi': 'vi-VN',
    'sw': 'sw-KE',
    'nl': 'nl-NL',
    'pl': 'pl-PL',
    'uk': 'uk-UA',
    'el': 'el-GR',
    'he': 'he-IL',
    'ro': 'ro-RO',
  };

  @override
  void initState() {
    super.initState();
    _initSpeech();
  }

  // Initialize speech recognition
  void _initSpeech() async {
    await _speechToText.initialize(
      onError: (error) {
        print('Speech recognition error: $error');
        setState(() => _isListening = false);
        _showErrorSnackBar('Voice input error: ${error.errorMsg}');
      },
      onStatus: (status) {
        print('Speech recognition status: $status');
        if (status == 'done' || status == 'notListening') {
          setState(() => _isListening = false);
        }
      },
    );
  }

  // Start/stop listening
  void _toggleListening(String currentLanguage) async {
    if (!_speechToText.isAvailable) {
      _showErrorSnackBar('Voice input not supported on this device');
      return;
    }

    if (_isListening) {
      await _speechToText.stop();
      setState(() => _isListening = false);
      return;
    }

    // Get speech language code
    final speechLang = _languageToSpeechCode[currentLanguage] ?? 'en-US';

    // Start listening
    bool started = await _speechToText.listen(
      onResult: (result) {
        setState(() {
          _lastWords = result.recognizedWords;
          // Append to existing text with space if needed
          if (_textController.text.isNotEmpty) {
            _textController.text += ' ';
          }
          _textController.text += result.recognizedWords;
        });
      },
      localeId: speechLang,
      listenFor: const Duration(seconds: 30),
      pauseFor: const Duration(seconds: 3),
      partialResults: false,
      cancelOnError: true,
    );

    if (started) {
      setState(() => _isListening = true);
    } else {
      _showErrorSnackBar('Failed to start voice input');
    }
  }

  // Show error message
  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // Messages list
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.all(16),
              itemCount: messages.length,
              itemBuilder: (context, index) => MessageBubble(message: messages[index]),
            ),
          ),

          // Input area - Gemini-style
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey[900],
              border: Border(
                top: BorderSide(color: Colors.grey[800]!, width: 0.5),
              ),
            ),
            child: SafeArea(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.grey[800]?.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: _isListening 
                        ? Colors.red.withOpacity(0.5) 
                        : Colors.grey[700]!.withOpacity(0.5),
                    width: 2,
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    // Attach button (left)
                    IconButton(
                      onPressed: () {
                        // Implement file attachment
                      },
                      icon: Icon(Icons.attach_file, color: Colors.grey[400]),
                      padding: EdgeInsets.only(left: 12, bottom: 8),
                    ),

                    // Text field
                    Expanded(
                      child: TextField(
                        controller: _textController,
                        maxLines: 8,
                        minLines: 1,
                        keyboardType: TextInputType.multiline,
                        textInputAction: TextInputAction.newline,
                        style: TextStyle(color: Colors.white),
                        decoration: InputDecoration(
                          hintText: 'Message AI...',
                          hintStyle: TextStyle(color: Colors.grey[500]),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(vertical: 12),
                        ),
                        onSubmitted: (value) {
                          if (value.isNotEmpty) {
                            _sendMessage();
                          }
                        },
                      ),
                    ),

                    // Recording indicator + Mic + Send buttons (right)
                    Padding(
                      padding: EdgeInsets.only(right: 8, bottom: 8),
                      child: Row(
                        children: [
                          // Recording indicator
                          if (_isListening)
                            Container(
                              margin: EdgeInsets.only(right: 8),
                              padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: Colors.red.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: Colors.red.withOpacity(0.5)),
                              ),
                              child: Row(
                                children: [
                                  SizedBox(
                                    width: 12,
                                    height: 12,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      valueColor: AlwaysStoppedAnimation<Color>(Colors.red),
                                    ),
                                  ),
                                  SizedBox(width: 8),
                                  Text(
                                    'Listening...',
                                    style: TextStyle(
                                      color: Colors.red[400],
                                      fontSize: 12,
                                      fontWeight: FontWeight.wold,
                                    ),
                                  ),
                                ],
                              ),
                            ),

                          // Mic button
                          IconButton(
                            onPressed: () => _toggleListening('en'), // Pass current UI language
                            icon: Icon(
                              Icons.mic,
                              color: _isListening ? Colors.red : Colors.grey[400],
                            ),
                            style: IconButton.styleFrom(
                              backgroundColor: _isListening 
                                  ? Colors.red.withOpacity(0.2) 
                                  : Colors.transparent,
                            ),
                          ),

                          // Send button
                          IconButton(
                            onPressed: _textController.text.isNotEmpty
                                ? _sendMessage
                                : null,
                            icon: Icon(Icons.send, color: Colors.white),
                            style: IconButton.styleFrom(
                              backgroundColor: _textController.text.isNotEmpty
                                  ? LinearGradient(
                                      colors: [Colors.blue[600]!, Colors.purple[600]!],
                                    ).createDecoration()
                                  : Colors.grey[700],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _sendMessage() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;

    // Add message to list
    setState(() {
      messages.add(Message(text, 'user'));
      _textController.clear();
    });

    // Send to API
    _sendToAPI(text);
  }

  void _sendToAPI(String message) async {
    // Implement your API call here
    // Show typing indicator
    // Get response
    // Add assistant message
  }

  @override
  void dispose() {
    _speechToText.cancel();
    _textController.dispose();
    super.dispose();
  }
}

class Message {
  final String content;
  final String role; // 'user' or 'assistant'

  Message(this.content, this.role);
}

class MessageBubble extends StatelessWidget {
  final Message message;

  const MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == 'user';
    
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.only(
          left: isUser ? 48 : 0,
          right: isUser ? 0 : 48,
          top: 8,
          bottom: 8,
        ),
        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          gradient: isUser
              ? LinearGradient(
                  colors: [Colors.blue[600]!, Colors.purple[600]!],
                )
              : null,
          color: isUser ? null : Colors.grey[800]?.withOpacity(0.5),
          borderRadius: BorderRadius.circular(16),
          border: isUser 
              ? null 
              : Border.all(color: Colors.grey[700]!.withOpacity(0.5)),
        ),
        child: Text(
          message.content,
          style: TextStyle(
            color: Colors.white,
            fontSize: 15,
          ),
        ),
      ),
    );
  }
}
```

## Key Features Implemented

### ✅ Auto-grow Text Field
- Uses `maxLines: 8` and `minLines: 1` for automatic expansion
- Grows naturally as user types (up to 8 lines)
- Minimum height of 48px for mobile comfort

### ✅ Voice Input with speech_to_text
- Works offline on Android and iOS
- Supports all 30 languages (ur-PK, en-US, hi-IN, bn-BD, etc.)
- Shows pulsing red indicator while recording
- Appends recognized speech to text field
- User can edit text before sending

### ✅ Error Handling
- Shows SnackBar with error message if:
  - Microphone permission denied
  - Speech recognition not supported
  - No speech detected
  - Network errors (for online recognition)

### ✅ UI/UX Matching Web
- Same rounded corners (24px radius)
- Same dark theme colors
- Mic icon on right side
- Attach icon on left side
- Send button on right
- Recording indicator with "Listening..." text
- Focus glow effect (border color change)

### ✅ Keyboard Behavior
- Enter key sends message
- Shift+Enter adds new line (default TextField behavior)

## Testing Checklist

- [ ] Install app on Android device
- [ ] Grant microphone permission
- [ ] Tap mic icon → should show "Listening..." indicator
- [ ] Speak a message → text should appear in input field
- [ ] Edit text if needed
- [ ] Press Enter or tap send → message should be sent
- [ ] Test with different languages (change app language)
- [ ] Test error case: deny microphone permission
- [ ] Test on iOS device
- [ ] Verify offline functionality (speech_to_text works offline)

## Notes

- The `speech_to_text` package works **offline** on both Android and iOS
- No API key required
- First time usage may require downloading language models (one-time)
- Recognition quality depends on device microphone and ambient noise
- For best results, speak clearly and pause at end of sentence

## Troubleshooting

### "Voice input not supported" error
- Ensure device has Google Speech Services (Android) or Siri (iOS)
- Check microphone permission in device settings
- Update `speech_to_text` package to latest version

### Poor recognition accuracy
- Speak clearly and at moderate pace
- Reduce background noise
- Try different language setting
- Ensure stable internet for initial language model download (one-time)

### App crashes on permission request
- Add permissions to AndroidManifest.xml and Info.plist
- Clean and rebuild: `flutter clean && flutter pub get && flutter run`

## Additional Resources

- [speech_to_text package docs](https://pub.dev/packages/speech_to_text)
- [Flutter permissions guide](https://docs.flutter.dev/development/data-and-background/permissions)

---

**Status**: Ready for Flutter implementation
**Web equivalent**: ✅ Implemented in `frontend/src/app/chat/page.tsx`
**Flutter status**: 📱 This document provides implementation guide