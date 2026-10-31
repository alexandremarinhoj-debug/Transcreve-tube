TRANScreveTube — pacote inicial de servidor

O que está incluído:
- Interface web em static/index.html
- Servidor Flask com rota POST /api/transcribe
- Consulta a serviço externo de legendas públicas (yt-transcript.net)

IMPORTANTE:
1. Este pacote ainda NÃO está publicado na internet.
2. O serviço externo é não oficial, pode limitar ou bloquear consultas e pode mudar.
3. A API oficial do YouTube não oferece extração livre de legendas de vídeos de terceiros.
4. Não há tradução nem download de arquivos neste projeto.
5. Antes de publicar para uso público, revise os termos do serviço externo, limites, privacidade e proteção contra abuso.

Teste local (computador com Python):
  pip install -r requirements.txt
  python app.py
Depois abra http://localhost:5000

Publicação:
- O projeto pode ser enviado a um host Python que aceite Flask/Gunicorn.
- Configure o comando de inicialização usando o Procfile.
- Não coloque credenciais secretas no HTML.
