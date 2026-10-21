import 'package:flutter_test/flutter_test.dart';
import 'package:labbox_mobile/main.dart';

void main() {
  testWidgets('Labbox TLS dashboard renders in Arabic', (tester) async {
    await tester.pumpWidget(const LabboxApp());
    expect(find.text('مركز فحص TLS'), findsOneWidget);
    expect(find.text('بدء فحص الشهادة'), findsOneWidget);
  });
}
