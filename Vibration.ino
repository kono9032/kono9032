void Vibration_measuring() {
  digitalWrite(6, HIGH);
  delay(50);
  digitalWrite(6, LOW);
  delay(150);
  digitalWrite(6, HIGH);
  delay(100);
  digitalWrite(6, LOW);
}
void Vibration_boot() {
  digitalWrite(6, HIGH);
  delay(250);
  digitalWrite(6, LOW);
  delay(350);
  digitalWrite(6, HIGH);
  delay(350);
  digitalWrite(6, LOW);
}
