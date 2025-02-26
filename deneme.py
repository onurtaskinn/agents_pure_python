import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "fal-ai/zonos",
    arguments={
        "reference_audio_url": "https://storage.googleapis.com/falserverless/model_tests/zonos/demo_voice_zonos.wav",
        "prompt": "Yazılım geliştirme dünyasında yapay zeka teknolojileri gerçek bir devrim yaratıyor. Araştırmalar, yapay zeka destekli araçların kullanımıyla geliştirme süreçlerinde yüzde kırka varan verimlilik artışı sağlandığını gösteriyor. Bu teknolojiler, kod yazma, test etme ve hata ayıklama gibi tekrarlayan görevlerde otomasyon sağlayarak geliştiricilerin daha stratejik çalışmalara odaklanmasına imkan veriyor. Ayrıca, yapay zeka algoritmaları, geleneksel yaklaşımlarla çözülmesi zor olan karmaşık problemlere yenilikçi çözümler sunuyor. Bu durum, yazılım geliştiricilerin çalışma şeklinde tam bir paradigma değişimi yaratıyor. Sonuç olarak, yapay zeka desteğiyle geliştirilen yazılımlar daha kaliteli, güvenli ve kullanıcı ihtiyaçlarına daha uygun hale geliyor."
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)