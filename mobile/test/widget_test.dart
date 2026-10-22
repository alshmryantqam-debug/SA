import 'package:flutter_test/flutter_test.dart';
import 'package:labbox_mobile/main.dart';

void main() {
  testWidgets('ONEBOX can open the Arabic TLS certificate lab', (tester) async {
    await tester.pumpWidget(const LabboxApp());
    expect(find.text('مختبر الشبكات الموحد'), findsOneWidget);
    await tester.tap(find.text('TLS').last);
    await tester.pumpAndSettle();
    expect(find.text('مركز فحص TLS'), findsOneWidget);
    expect(find.text('بدء فحص الشهادة'), findsOneWidget);
  });
}
