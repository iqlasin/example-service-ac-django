from django.db import models

class Harga(models.Model):
    service_ac = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Harga: {self.service_ac}"

class User(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('teknisi', 'Teknisi'),
    ]
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    alamat = models.TextField()
    nomor_hp = models.CharField(max_length=15)

    def __str__(self):
        return self.username

class Teknisi(models.Model):
    nama = models.CharField(max_length=50)
    alamat = models.TextField()
    nomor_hp = models.CharField(max_length=15)
    spesialisasi = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nama

class Service(models.Model):
    STATUS_CHOICES = [
        ('menunggu', 'Menunggu'),
        ('dikerjakan', 'Dikerjakan'),
        ('selesai', 'Selesai'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    teknisi = models.ForeignKey(Teknisi, on_delete=models.CASCADE, related_name='services', null=True, blank=True)
    tanggal_servis = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    deskripsi = models.TextField()

    def __str__(self):
        return f"Service {self.id} - {self.status}"

