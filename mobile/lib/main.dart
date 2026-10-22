import 'dart:io';
import 'package:flutter/material.dart';

void main() => runApp(const LabboxApp());

const bg = Color(0xFF0B0813);
const panel = Color(0xFF191326);
const purple = Color(0xFFB17CFF);
const muted = Color(0xFFB9ADC9);
const edge = Color(0xFF3A2A50);

class LabboxApp extends StatelessWidget {
  const LabboxApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'ONEBOX | Cyber Network Lab',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(useMaterial3: true, brightness: Brightness.dark,
      scaffoldBackgroundColor: bg,
      colorScheme: ColorScheme.fromSeed(seedColor: purple, brightness: Brightness.dark),
      inputDecorationTheme: InputDecorationTheme(filled: true, fillColor: panel,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: edge)))),
    home: const Directionality(textDirection: TextDirection.rtl, child: OneboxHome()));
}

class OneboxHome extends StatefulWidget {
  const OneboxHome({super.key});
  @override
  State<OneboxHome> createState() => _OneboxHomeState();
}

class _OneboxHomeState extends State<OneboxHome> {
  int tab = 0;
  final routerHost = TextEditingController(text: '192.168.88.1');
  final routerPort = TextEditingController(text: '8728');
  final tlsHost = TextEditingController(text: 'example.com');
  final tlsPort = TextEditingController(text: '443');
  final hex = TextEditingController();
  bool busy = false;
  bool tlsBusy = false;
  String routerStatus = 'لم يتم اختبار الاتصال بعد';
  String packetStatus = 'ألصق بايتات Hex لتفسير ترويسة سجل TLS.';
  String? tlsError;
  X509Certificate? cert;
  String? tlsTarget;

  @override
  void dispose() {
    routerHost.dispose(); routerPort.dispose(); tlsHost.dispose(); tlsPort.dispose(); hex.dispose();
    super.dispose();
  }

  Future<void> probePort() async {
    final h = routerHost.text.trim();
    final p = int.tryParse(routerPort.text.trim());
    if (h.isEmpty || p == null || p < 1 || p > 65535) {
      setState(() => routerStatus = 'أدخل عنواناً ومنفذاً صحيحين.'); return;
    }
    setState(() { busy = true; routerStatus = 'جارٍ اختبار TCP على ' + h + ':' + p.toString(); });
    Socket? s;
    try {
      s = await Socket.connect(h, p, timeout: const Duration(seconds: 4));
      if (mounted) setState(() => routerStatus =
        'منفذ TCP متاح. هذا لا يثبت نجاح تسجيل الدخول أو جلسة RouterOS API.');
    } on Object catch (e) {
      if (mounted) setState(() => routerStatus = 'تعذر الوصول: ' + e.toString());
    } finally { s?.destroy(); if (mounted) setState(() => busy = false); }
  }

  Future<void> inspectTls() async {
    final h = tlsHost.text.trim();
    final p = int.tryParse(tlsPort.text.trim());
    if (h.isEmpty || h.contains(RegExp(r'[\s/\\]')) || h.contains('://')) {
      setState(() => tlsError = 'أدخل اسم نطاق صحيحاً دون https:// أو مسار.'); return;
    }
    if (p == null || p < 1 || p > 65535) {
      setState(() => tlsError = 'المنفذ يجب أن يكون بين 1 و65535.'); return;
    }
    setState(() { tlsBusy = true; tlsError = null; cert = null; tlsTarget = null; });
    SecureSocket? s;
    try {
      s = await SecureSocket.connect(h, p, timeout: const Duration(seconds: 10));
      final c = s.peerCertificate;
      if (c == null) throw const SocketException('لم يرسل الخادم شهادة.');
      if (mounted) setState(() { cert = c; tlsTarget = h + ':' + p.toString(); });
    } on Object catch (e) {
      if (mounted) setState(() => tlsError = 'تعذر اتصال TLS موثّق.\n' + e.toString());
    } finally { s?.destroy(); if (mounted) setState(() => tlsBusy = false); }
  }

  void parseTlsHeader() {
    final clean = hex.text.replaceAll(RegExp(r'[^0-9a-fA-F]'), '');
    if (clean.length < 10 || clean.length.isOdd) {
      setState(() => packetStatus = 'أدخل 5 بايتات على الأقل، مثال: 16 03 03 00 05'); return;
    }
    final b = <int>[];
    for (var i = 0; i < clean.length; i += 2) {
      b.add(int.parse(clean.substring(i, i + 2), radix: 16));
    }
    const names = {20:'Change Cipher Spec',21:'Alert',22:'Handshake',23:'Application Data (مشفّر)'};
    final name = names[b[0]] ?? 'نوع سجل غير معروف';
    final version = b[1].toString() + '.' + b[2].toString();
    final length = b[3] * 256 + b[4];
    setState(() => packetStatus = 'نوع السجل: ' + name + '\nإصدار الترويسة: ' + version +
      '\nطول الحمولة المعلن: ' + length.toString() + ' بايت\nالبايتات المدخلة: ' +
      b.length.toString() + '\n\nتحليل ترويسة أولي فقط؛ لا يفك تشفير الحمولة ولا يثبت أن البيانات حزمة كاملة.');
  }

  @override
  Widget build(BuildContext context) {
    final views = [_dashboard(), _routerPage(), _packetPage(), _tlsPage(), _toolsPage()];
    return Scaffold(
      body: SafeArea(child: Column(children: [
        _header(),
        Expanded(child: AnimatedSwitcher(duration: const Duration(milliseconds: 200),
          child: KeyedSubtree(key: ValueKey(tab), child: views[tab]))),
      ])),
      bottomNavigationBar: NavigationBar(backgroundColor: panel,
        indicatorColor: purple.withValues(alpha: .22), selectedIndex: tab,
        onDestinationSelected: (v) => setState(() => tab = v),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_rounded), label: 'الرئيسية'),
          NavigationDestination(icon: Icon(Icons.router_rounded), label: 'MikroTik'),
          NavigationDestination(icon: Icon(Icons.data_object_rounded), label: 'الحزم'),
          NavigationDestination(icon: Icon(Icons.verified_user_rounded), label: 'TLS'),
          NavigationDestination(icon: Icon(Icons.security_rounded), label: 'الأدوات'),
        ]),
    );
  }

  Widget _header() => Padding(padding: const EdgeInsets.fromLTRB(18,14,18,12),
    child: Row(children: [
      Container(width:46,height:46,decoration:BoxDecoration(
        gradient:const LinearGradient(colors:[Color(0xFFD0A9FF),Color(0xFF7135C7)]),
        borderRadius:BorderRadius.circular(15)),
        child:const Icon(Icons.hub_rounded,color:Colors.white,size:27)),
      const SizedBox(width:12),
      const Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text('ONEBOX',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900,letterSpacing:2)),
        Text('CYBER NETWORK LAB • ANDROID',style:TextStyle(color:muted,fontSize:9,letterSpacing:1)),
      ])),
      const Icon(Icons.shield_moon_outlined,color:purple,size:27),
    ]));

  Widget _dashboard() => ListView(padding:const EdgeInsets.fromLTRB(18,8,18,24),children:[
    Container(padding:const EdgeInsets.all(21),decoration:BoxDecoration(
      gradient:const LinearGradient(begin:Alignment.topRight,end:Alignment.bottomLeft,
        colors:[Color(0xFF382452),Color(0xFF1B1429),Color(0xFF11101A)]),
      borderRadius:BorderRadius.circular(26),border:Border.all(color:edge)),
      child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        const Text('مختبر الشبكات الموحد',style:TextStyle(fontSize:24,fontWeight:FontWeight.w900)),
        const SizedBox(height:8),
        const Text('لوحة واحدة لتشخيص الشبكة، اختبار الوصول إلى MikroTik، وفحص شهادات TLS وتحليل ترويسات السجلات.',
          style:TextStyle(color:muted,height:1.55)),
        const SizedBox(height:18),
        Row(children:[
          _metric('RO','اختبار راوتر'),_metric('TLS','شهادة'),_metric('HEX','ترويسة حزم'),
        ]),
      ])),
    const SizedBox(height:22),
    _section('مركز العمليات','الوحدات المتاحة في هذه النسخة'),
    const SizedBox(height:10),
    _tile(Icons.router_rounded,'MikroTik Lab','اختبار وصول TCP إلى الراوتر التجريبي',()=>setState(()=>tab=1)),
    _tile(Icons.data_object_rounded,'Packet Inspector','تحليل أولي لترويسة TLS من Hex',()=>setState(()=>tab=2)),
    _tile(Icons.verified_user_rounded,'TLS Certificate Lab','فحص شهادة اتصال موثّق',()=>setState(()=>tab=3)),
    _tile(Icons.security_rounded,'Cyber Toolkit','أدوات التشخيص وخارطة الوحدات',()=>setState(()=>tab=4)),
    const SizedBox(height:8),
    _notice('مختبر مصرح به','استخدم الأدوات على راوتر تملكه أو لديك إذن بفحصه. لا يمكن فك TLS بمجرد التقاط الحزم.'),
  ]);

  Widget _routerPage() => ListView(padding:const EdgeInsets.all(18),children:[
    _heading(Icons.router_rounded,'مختبر MikroTik','اختبار قابلية الوصول إلى منفذ API'),
    const SizedBox(height:16),
    _field(routerHost,'عنوان الراوتر',Icons.lan_rounded,TextInputType.url),
    const SizedBox(height:12),
    _field(routerPort,'منفذ API',Icons.settings_ethernet,TextInputType.number),
    const SizedBox(height:14),
    _button(busy?'جارٍ الاختبار...':'اختبار وصول TCP',busy?null:probePort),
    const SizedBox(height:14),_result(routerStatus),
    const SizedBox(height:14),
    _notice('حدود الاختبار','نجاح TCP لا يعني تسجيل الدخول أو عمل RouterOS API. هذه الوحدة لا تعدّل إعدادات الراوتر ولا تنفّذ أوامر إدارة بعد.'),
    const SizedBox(height:18),
    _section('الوحدات التالية','لن نعرضها كميزات مكتملة قبل تنفيذها'),
    _tile(Icons.monitor_heart_outlined,'حالة الراوتر','CPU والذاكرة والواجهات — تتطلب جلسة API موثّقة.',()=>_info('قراءة حالة الراوتر لم تُنفّذ بعد.')),
    _tile(Icons.people_alt_outlined,'المشتركون والطوابير','قراءة PPP وHotspot وQueues.',()=>_info('قراءة المشتركين والطوابير لم تُنفّذ بعد.')),
  ]);

  Widget _packetPage() => ListView(padding:const EdgeInsets.all(18),children:[
    _heading(Icons.data_object_rounded,'Packet Inspector','تحليل ترويسة سجل TLS من bytes'),
    const SizedBox(height:14),
    const Text('ألصق بايتات سداسية عشرية. مثال: 16 03 03 00 05. هذه ليست أداة التقاط حي أو محلل PCAP كامل.',
      style:TextStyle(color:muted,height:1.55)),
    const SizedBox(height:14),
    TextField(controller:hex,minLines:4,maxLines:8,textDirection:TextDirection.ltr,
      decoration:const InputDecoration(labelText:'بيانات Hex',hintText:'16 03 03 00 05 ...',alignLabelWithHint:true)),
    const SizedBox(height:12),_button('تحليل ترويسة TLS',parseTlsHeader),
    const SizedBox(height:14),_result(packetStatus),
    const SizedBox(height:14),
    _notice('البيانات المشفرة','TLS Application Data تبقى مشفرة. فكها يتطلب أسرار جلسة أو مفاتيح مناسبة ضمن مختبر مصرح به.'),
  ]);

  Widget _tlsPage() => ListView(padding:const EdgeInsets.all(18),children:[
    _heading(Icons.verified_user_rounded,'مركز فحص TLS','اتصال موثّق وبيانات الشهادة العامة'),
    const SizedBox(height:14),
    _field(tlsHost,'اسم النطاق',Icons.language_rounded,TextInputType.url),
    const SizedBox(height:12),
    _field(tlsPort,'المنفذ',Icons.settings_ethernet,TextInputType.number),
    const SizedBox(height:14),
    _button(tlsBusy?'جارٍ فحص الشهادة...':'بدء فحص الشهادة',tlsBusy?null:inspectTls),
    if(tlsError!=null)...[const SizedBox(height:14),_result(tlsError!)],
    if(cert!=null)...[
      const SizedBox(height:14),
      _result('تم الاتصال: ' + (tlsTarget??'') + '\n\nالاسم: ' + cert!.subject +
        '\n\nالجهة المصدرة: ' + cert!.issuer + '\n\nصالحة من: ' +
        cert!.startValidity.toUtc().toIso8601String() + '\n\nتنتهي في: ' +
        cert!.endValidity.toUtc().toIso8601String() + '\n\nSHA-1: ' + cert!.sha1.toString()),
    ],
    const SizedBox(height:14),
    _notice('التحقق يبقى مفعّلاً','لا يعطّل التطبيق التحقق من الشهادات ولا يتجاوز حماية التطبيقات.'),
  ]);

  Widget _toolsPage() => ListView(padding:const EdgeInsets.all(18),children:[
    _heading(Icons.security_rounded,'Cyber Toolkit','أدوات تشخيص ضمن بيئة مصرح بها'),
    const SizedBox(height:14),
    _tile(Icons.dns_rounded,'DNS diagnostics','وحدة فحص DNS — مخططة وليست جاهزة.',()=>_info('أداة DNS غير منفّذة بعد.')),
    _tile(Icons.radar_rounded,'TCP reachability','اختبار منفذ على جهاز مصرح.',()=>setState(()=>tab=1)),
    _tile(Icons.verified_user_outlined,'Certificate audit','تحقق من شهادة TLS وبياناتها العامة.',()=>setState(()=>tab=3)),
    _tile(Icons.folder_open_rounded,'PCAP analysis','تحليل ملفات الالتقاط المحلي — يحتاج محللاً مخصصاً.',()=>_info('تحليل PCAP الكامل لم يُنفّذ بعد.')),
    const SizedBox(height:12),
    _notice('مبدأ التطوير','كل أداة ستصبح متاحة عند ربطها بمحرك حقيقي واختبارها؛ لن تكون هناك أزرار وهمية.'),
  ]);

  Widget _heading(IconData icon,String title,String subtitle)=>Row(crossAxisAlignment:CrossAxisAlignment.start,children:[
    Container(width:48,height:48,decoration:BoxDecoration(color:purple.withValues(alpha:.14),borderRadius:BorderRadius.circular(15)),
      child:Icon(icon,color:purple,size:26)),
    const SizedBox(width:12),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text(title,style:const TextStyle(fontSize:22,fontWeight:FontWeight.w900)),
      const SizedBox(height:5),Text(subtitle,style:const TextStyle(color:muted,height:1.4)),
    ])),
  ]);

  Widget _metric(String value,String label)=>Expanded(child:Container(
    margin:const EdgeInsetsDirectional.only(end:7),padding:const EdgeInsets.symmetric(vertical:12,horizontal:6),
    decoration:BoxDecoration(color:Colors.black.withValues(alpha:.17),borderRadius:BorderRadius.circular(14)),
    child:Column(children:[Text(value,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:18,color:purple)),
      const SizedBox(height:3),Text(label,style:const TextStyle(fontSize:10,color:muted))])));

  Widget _section(String title,String subtitle)=>Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
    Text(title,style:const TextStyle(fontSize:17,fontWeight:FontWeight.w800)),
    const SizedBox(height:4),Text(subtitle,style:const TextStyle(color:muted,fontSize:12)),
  ]);

  Widget _tile(IconData icon,String title,String subtitle,VoidCallback action)=>Container(
    margin:const EdgeInsets.only(bottom:10),
    decoration:BoxDecoration(color:panel,borderRadius:BorderRadius.circular(17),border:Border.all(color:edge)),
    child:ListTile(onTap:action,contentPadding:const EdgeInsets.symmetric(horizontal:14,vertical:5),
      leading:Container(width:44,height:44,decoration:BoxDecoration(color:purple.withValues(alpha:.13),borderRadius:BorderRadius.circular(13)),
        child:Icon(icon,color:purple)),
      title:Text(title,style:const TextStyle(fontWeight:FontWeight.w800)),
      subtitle:Padding(padding:const EdgeInsets.only(top:4),child:Text(subtitle,style:const TextStyle(color:muted,fontSize:12,height:1.4))),
      trailing:const Icon(Icons.chevron_left_rounded,color:muted)));

  Widget _field(TextEditingController c,String label,IconData icon,TextInputType type)=>TextField(
    controller:c,keyboardType:type,textDirection:TextDirection.ltr,
    decoration:InputDecoration(labelText:label,prefixIcon:Icon(icon)));

  Widget _button(String label,VoidCallback? action)=>SizedBox(height:52,width:double.infinity,
    child:FilledButton.icon(onPressed:action,icon:const Icon(Icons.play_arrow_rounded),label:Text(label,
      style:const TextStyle(fontWeight:FontWeight.w800)),
      style:FilledButton.styleFrom(backgroundColor:purple,foregroundColor:Colors.white,
        shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(15)))));

  Widget _result(String text)=>Container(width:double.infinity,padding:const EdgeInsets.all(16),
    decoration:BoxDecoration(color:panel,borderRadius:BorderRadius.circular(16),border:Border.all(color:edge)),
    child:SelectableText(text,style:const TextStyle(height:1.55)));

  Widget _notice(String title,String body)=>Container(padding:const EdgeInsets.all(14),
    decoration:BoxDecoration(color:const Color(0xFF211A2B),borderRadius:BorderRadius.circular(15),
      border:Border.all(color:const Color(0xFF57406C))),
    child:Row(crossAxisAlignment:CrossAxisAlignment.start,children:[
      const Icon(Icons.info_outline_rounded,color:purple),const SizedBox(width:10),
      Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text(title,style:const TextStyle(fontWeight:FontWeight.w800)),const SizedBox(height:4),
        Text(body,style:const TextStyle(color:muted,height:1.45,fontSize:12)),
      ])),
    ]));

  void _info(String text)=>showDialog<void>(context:context,builder:(context)=>AlertDialog(
    backgroundColor:panel,title:const Text('حالة الوحدة'),content:Text(text),
    actions:[TextButton(onPressed:()=>Navigator.pop(context),child:const Text('حسناً'))]));
}
