# Vfsbot

## Spyke Turizm giriş ekranını veritabanı ile çalıştırma (macOS)

1. Terminal açın ve proje klasörüne girin:

```bash
cd /workspace/Vfsbot
```

2. Sunucuyu başlatın:

```bash
python3 server.py
```

3. Tarayıcıdan açın:

```text
http://localhost:4173
```

> Durdurmak için terminalde `Ctrl + C`.

## Varsayılan giriş bilgisi

- Kullanıcı adı: `Furkan Kutas`
- Şifre: `Furkan13!`

## Veritabanı bilgisi

- Uygulama açıldığında otomatik `spyke.db` SQLite veritabanı oluşturulur.
- `users` tablosu giriş kullanıcılarını tutar.
- `passport_images` tablosu ileride pasaport görsellerini saklamak için hazırdır.

## Logo kullanımı

- Sol panelde şu anda bir logo yer tutucu var.
- Logo dosyanızı projeye ekleyip `index.html` içinde `logo-placeholder` bölümünü `<img>` ile değiştirebilirsiniz.
