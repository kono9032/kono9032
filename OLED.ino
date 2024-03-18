void draw(void) {
  u8g.drawBitmapP(0, 0, 4, 9, icon);
}

void oled_image() {
  u8g.firstPage();
  do {
    draw();
    u8g.setFont(u8g_font_helvR08);
    u8g.setPrintPos(44, 8);
    u8g.print("CODE: ");
    u8g.print(RFID_uid);
    // or u8g.drawStr(x,y,"내용");
    u8g.setFont(u8g_font_fur42n);
    u8g.setPrintPos(0, 58);
    u8g.print(value, 1);
    u8g.setFont(u8g_font_fur11);
    u8g.setPrintPos(110, 60);
    u8g.print("C");
    u8g.setPrintPos(123, 60);
    u8g.write(0xb0);
  }
  while ( u8g.nextPage() );
}

void oled_boot() {
  u8g.firstPage();
  do {
    u8g.setFont(u8g_font_helvR08);
    u8g.setPrintPos(42, 35);
    u8g.print("K O B E C");
  }
  while ( u8g.nextPage() );
}
