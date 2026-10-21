import 'dart:io';

import 'package:flutter/material.dart';

void main() => runApp(const LabboxApp());

const bg = Color(0xFF100B1C);
const panel = Color(0xFF1C142B);
const purple = Color(0xFFA56AFF);
const muted = Color(0xFFB8A9CA);

class LabboxApp extends StatelessWidget {
  const LabboxApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LABBOX | مختبر الشبكة',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: bg,
        colorScheme: ColorScheme.fromSeed(seedColor: purple, brightness: Brightness.dark),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: panel,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Color(0xFF49345F))),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Color(0xFF49345F))),
        ),
      ),
      home: const Directionality(textDirection: TextDirection.rtl, child: HomePage()),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final hostController = TextEditingController(text: 'example.com');
  final portController = TextEditingController(text: '443');
  bool busy = false;
  String? error;
  X509Certificate? certificate;
  String? checkedHost;

  @override
  void dispose() {
    hostController.dispose();
    portController.dispose();
    super.dispose();
  }

  Future<void> inspectCertificate() async {
    final host = hostController.text.trim();
    final port = int.tryParse(portController.text.trim());
    if (host.isEmpty || host.contains(RegExp(r'[\s/\\]')) || host.contains('://')) {
      setState(() => error = 'أدخل اسم نطاق صحيحاً دون https:// أو مسار.');
      return;
    }
    if (port == null || port < 1 || port > 65535) {
      setState(() => error = 'المنفذ يجب أن يكون رقماً بين 1 و65535.');
      return;
    }
    setState(() { busy = true; error = null; certificate = null; checkedHost = null; });
    SecureSocket? socket;
    try {
      socket = await SecureSocket.connect(host, port, timeout: const Duration(seconds: 10));
      final cert = socket.peerCertificate;
      if (cert == null) throw const SocketException('لم يقدم الخادم شهادة يمكن قراءتها.');
      if (!mounted) return;
      setState(() { certificate = cert; checkedHost = '$host:$port'; });
    } on Object catch (e) {
      if (!mounted) return;
      setState(() => error = 'تعذّر إتمام اتصال TLS الآمن. تحقق من النطاق والمنفذ والشهادة والإنترنت.\nالتفاصيل: $e');
    } finally {
      socket?.destroy();
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 16, 18, 28),
          children: [
            Row(children: [
              Container(width: 48, height: 48, decoration: BoxDecoration(gradient: const LinearGradient(colors: [purple, Color(0xFF6337B8)]), borderRadius: BorderRadius.circular(16)), child: const Icon(Icons.radar_rounded, color: Colors.white, size: 28)),
              const SizedBox(width: 12),
              const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('LABBOX', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 2)),
                Text('مختبر تشخيص الشبكة الآمن', style: TextStyle(color: muted, fontSize: 12)),
              ])),
              const Icon(Icons.verified_user_outlined, color: purple, size: 26),
            ]),
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(begin: Alignment.topRight, end: Alignment.bottomLeft, colors: [Color(0xFF302047), panel, Color(0xFF171021)]),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: const Color(0xFF49345F)),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('مركز فحص TLS', style: TextStyle(fontSize: 23, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                const Text('افحص شهادة اتصال آمن، والجهة المصدرة، وفترة صلاحيتها. التحقق من الشهادة يبقى مفعّلاً.', style: TextStyle(color: muted, height: 1.5)),
                const SizedBox(height: 20),
                TextField(controller: hostController, textDirection: TextDirection.ltr, keyboardType: TextInputType.url, decoration: const InputDecoration(labelText: 'اسم النطاق', hintText: 'example.com', prefixIcon: Icon(Icons.language))),
                const SizedBox(height: 12),
                TextField(controller: portController, textDirection: TextDirection.ltr, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'المنفذ', prefixIcon: Icon(Icons.settings_ethernet))),
                const SizedBox(height: 16),
                SizedBox(width: double.infinity, height: 52, child: FilledButton.icon(
                  onPressed: busy ? null : inspectCertificate,
                  icon: busy ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.shield_outlined),
                  label: Text(busy ? 'جارٍ فحص الاتصال...' : 'بدء فحص الشهادة', style: const TextStyle(fontWeight: FontWeight.bold)),
                  style: FilledButton.styleFrom(backgroundColor: purple, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
                )),
              ]),
            ),
            const SizedBox(height: 18),
            if (error != null) _messageCard(Icons.error_outline, 'تعذر الفحص', error!, const Color(0xFFFF7B86)),
            if (certificate != null) _resultCard(),
            const SizedBox(height: 18),
            _feature(Icons.lock_outline, 'اتصال TLS موثّق', 'لا يتم تعطيل التحقق من الشهادات أو تجاوز حماية التطبيقات.'),
            _feature(Icons.visibility_outlined, 'بيانات عامة فقط', 'يعرض بيانات الشهادة؛ لا يلتقط أو يفك تشفير محتوى HTTPS.'),
            _feature(Icons.phone_android, 'نسخة Android', 'واجهة موبايل أولية قابلة للبناء كملف APK من GitHub Actions.'),
            const SizedBox(height: 12),
            const Center(child: Text('استخدم الفحص فقط على نطاق تملكه أو لديك إذن بفحصه.', textAlign: TextAlign.center, style: TextStyle(color: muted, fontSize: 11))),
          ],
        ),
      ),
    );
  }

  Widget _resultCard() {
    final cert = certificate!;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(color: panel, borderRadius: BorderRadius.circular(20), border: Border.all(color: const Color(0xFF3C795D))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Row(children: [Icon(Icons.check_circle, color: Color(0xFF6CE0A4)), SizedBox(width: 8), Text('تم إنشاء اتصال TLS والتحقق من الشهادة', style: TextStyle(fontWeight: FontWeight.bold))]),
        const SizedBox(height: 8),
        Text(checkedHost ?? '', textDirection: TextDirection.ltr, style: const TextStyle(color: muted)),
        const SizedBox(height: 14),
        _detail('الاسم', cert.subject),
        _detail('الجهة المصدرة', cert.issuer),
        _detail('صالحة من', cert.startValidity.toUtc().toIso8601String()),
        _detail('تنتهي في', cert.endValidity.toUtc().toIso8601String()),
        _detail('بصمة SHA-1 للشهادة', cert.sha1.toString()),
        const SizedBox(height: 8),
        const Text('ملاحظة: هذه بيانات الشهادة فقط وليست التقاطاً لمحتوى الاتصال.', style: TextStyle(color: muted, fontSize: 12)),
      ]),
    );
  }

  Widget _detail(String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(color: muted, fontSize: 12)),
      const SizedBox(height: 3),
      SelectableText(value, textDirection: TextDirection.ltr, style: const TextStyle(fontSize: 13)),
    ]),
  );

  Widget _messageCard(IconData icon, String title, String message, Color color) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(color: panel, borderRadius: BorderRadius.circular(16), border: Border.all(color: color.withValues(alpha: .5))),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Icon(icon, color: color), const SizedBox(width: 10),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: TextStyle(color: color, fontWeight: FontWeight.bold)),
        const SizedBox(height: 6), SelectableText(message, style: const TextStyle(height: 1.4)),
      ])),
    ]),
  );

  Widget _feature(IconData icon, String title, String body) => Container(
    margin: const EdgeInsets.only(bottom: 10),
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(color: panel, borderRadius: BorderRadius.circular(16), border: Border.all(color: const Color(0xFF352746))),
    child: Row(children: [
      Container(width: 42, height: 42, decoration: BoxDecoration(color: purple.withValues(alpha: .13), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: purple)),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4), Text(body, style: const TextStyle(color: muted, fontSize: 12, height: 1.4)),
      ])),
    ]),
  );
}
