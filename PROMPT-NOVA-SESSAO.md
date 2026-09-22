# Prompt para colar numa conversa nova (Opus 5) — executa o BLOCO 2 de qualquer pasta

```
Você vai executar um projeto que já está planejado. Não me pergunte nada: decida, registre a premissa e siga.

PASTA DO PROJETO: C:\Users\NOTE\Desktop\Projetos\gta6-canais
Se você tiver a ferramenta de mudar de diretório, mude para essa pasta agora. Se não tiver, use SEMPRE caminhos absolutos começando por C:\Users\NOTE\Desktop\Projetos\gta6-canais\ em todo comando, leitura e escrita. Nunca crie arquivo fora dela (exceto o Cérebro, no fim).

LEIA PRIMEIRO, nesta ordem, inteiros:
1. C:\Users\NOTE\Desktop\Projetos\gta6-canais\RETOMAR.md
2. C:\Users\NOTE\Desktop\Projetos\gta6-canais\PLANO.md
3. C:\Users\NOTE\Desktop\Projetos\gta6-canais\VICESCALE.md
4. C:\Users\NOTE\Desktop\Projetos\gta6-canais\ARQUITETURA.md
5. C:\Users\NOTE\Desktop\Projetos\gta6-canais\PROMPT.md — só o BLOCO 2
6. C:\Users\NOTE\Desktop\Projetos\Palavra-Viva-3x\CLAUDE.md (o motor que será copiado)
7. C:\Users\NOTE\Desktop\Projetos\psicologia-fria\CLAUDE.md (publicação no Instagram)

O QUE FAZER: executar o BLOCO 2 do PROMPT.md inteiro, na ordem dos 14 passos, seguindo ARQUITETURA.md como especificação. O BLOCO 1 já foi executado: ARQUITETURA.md, conteudo/fatos/*.json (150 fatos) e conteudo/frases.json já existem e não se reescrevem.

REGRAS:
- Responda sempre em português.
- Permissão total para ferramentas: não pare para pedir confirmação.
- Custo zero: GitHub Actions em repo público, edge-tts, ffmpeg, yt-dlp, galeria oficial da Rockstar. Nenhuma assinatura.
- Arquivo de vídeo só de fonte limpa (trailers oficiais, Extended Look, galeria; depois de 19/11, gameplay com licença Creative Commons, com crédito). Vídeo de outra página serve para medir, nunca para postar.
- O repo git já existe na pasta (remoto: github.com/<conta do Diego>/gta6-canais, privado). Commite a cada passo concluído com mensagem curta e faça push. Ao final, se os workflows precisarem de minutos ilimitados, deixe anotado em RETOMAR.md que o repo deve virar público antes de ligar o cron.
- Quando um passo depender de mim (conta Google nova, token, Zernio, Página do Facebook, links da Shopee), deixe o código pronto para rodar assim que o secret existir, escreva a instrução em PENDENCIAS-DIEGO.md e siga para o próximo passo.
- Para a Shopee (passo 7 do BLOCO 2), use o Chrome pela extensão do Claude: a conta de afiliado já está logada. Se não conseguir gerar os links, deixe a lista de produtos com URL, preço, "vendidos" e comissão em conteudo/ofertas.json e a geração do link entra em PENDENCIAS-DIEGO.md.
- Antes de terminar: python -m unittest discover -s testes tem de passar; RETOMAR.md atualizado (o que está no ar, o que falta em ordem, pendências minhas); nota "GTA 6 - canais automáticos" em C:\Users\NOTE\Desktop\Cérebro\50 Canais e Automações\ atualizada com o estado, commit e push do Cérebro também.

RELATÓRIO FINAL (em português, curto): o que está pronto e testado; o que está pronto esperando secret; o que ficou de fora e por quê; e a lista numerada do que EU tenho de fazer, passo a passo, com o link de cada site.
```
