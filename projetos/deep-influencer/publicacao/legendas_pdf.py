"""Gera o PDF com legendas de teste para os Reels do DEEP (identidade visual da marca)."""
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

FONTES = sys.argv[1] if len(sys.argv) > 1 else "fonts"
SAIDA = sys.argv[2] if len(sys.argv) > 2 else "DEEP_legendas_reels_teste.pdf"
for nome, arq in [("Serif", "PlayfairMedium"), ("SerifIt", "PlayfairItalic"), ("Black", "InterBlack"),
                  ("XBold", "InterExtraBold"), ("Medium", "InterMedium"), ("Regular", "InterRegular")]:
    pdfmetrics.registerFont(TTFont(nome, f"{FONTES}/{arq}.ttf"))
# <b> e <i> dentro dos parágrafos
registerFontFamily("Regular", normal="Regular", bold="XBold", italic="SerifIt", boldItalic="XBold")

TINTA = HexColor("#2B2521")
SUAVE = HexColor("#7A6F66")
AMARELO = HexColor("#FCEDC0")
AMARELO_ESC = HexColor("#B8A26A")
LINHA = HexColor("#E8E1D6")

st = {
    "capa_marca": ParagraphStyle("m", fontName="Medium", fontSize=9, leading=12, textColor=SUAVE, spaceAfter=10, wordSpace=0),
    "capa_titulo": ParagraphStyle("t", fontName="Serif", fontSize=30, leading=34, textColor=TINTA),
    "capa_sub": ParagraphStyle("s", fontName="SerifIt", fontSize=14, leading=19, textColor=SUAVE, spaceBefore=6),
    "h1": ParagraphStyle("h1", fontName="Black", fontSize=15, leading=19, textColor=TINTA, spaceAfter=2),
    "h1sub": ParagraphStyle("h1s", fontName="SerifIt", fontSize=11, leading=15, textColor=SUAVE, spaceAfter=8),
    "tag": ParagraphStyle("tag", fontName="XBold", fontSize=7.5, leading=10, textColor=TINTA),
    "legenda": ParagraphStyle("l", fontName="Regular", fontSize=10, leading=14.5, textColor=TINTA),
    "gancho": ParagraphStyle("g", fontName="XBold", fontSize=10.5, leading=14.5, textColor=TINTA),
    "nota": ParagraphStyle("n", fontName="Regular", fontSize=8.5, leading=12, textColor=SUAVE),
    "corpo": ParagraphStyle("c", fontName="Regular", fontSize=10, leading=15, textColor=TINTA, alignment=TA_LEFT),
    "item": ParagraphStyle("i", fontName="Regular", fontSize=10, leading=15, textColor=TINTA, leftIndent=12,
                           bulletIndent=0, spaceAfter=3),
}

HASH_BASE = "#influenciadordigital #criadordeconteudo #marketingdeinfluencia"

CORTES = [
    ("01", "O sonho vs. a realidade", "Como ser influencer: o sonho vs. a realidade", [
        ("A · Curiosidade", "Metade dos influenciadores do Brasil ganha até R$ 5 mil por mês.",
         "E isso é quem já monetiza. Quase 30% nem conseguem. Assiste até o fim antes de largar tudo "
         "pra virar influencer.", "#comoserinfluencer #influenciadordigital #criadordeconteudo"),
        ("B · Opinião forte", "Viver de publi não é ter negócio. É ter cachê.",
         "E cachê acaba quando o algoritmo muda, quando a marca troca de estratégia ou quando chega "
         "alguém mais novo. Concorda ou discorda? Me conta aqui embaixo.", HASH_BASE),
        ("C · Compartilhamento", "Manda pra aquela pessoa que quer largar tudo pra ser influencer.",
         "Não é pra desanimar. É pra ela entrar sabendo os números reais.",
         "#influencer #vidadeinfluencer #instagram"),
    ]),
    ("02", "Por que todo mundo quer entrar", "Por que todo mundo quer ser influencer?", [
        ("A · Curiosidade", "Você vê a viagem. Não vê os 18 meses postando sem retorno.",
         "A narrativa que circula é sempre a de quem deu certo. Esse é o lado que ninguém mostra.",
         "#bastidores #criadordeconteudo #influenciadordigital"),
        ("B · Opinião forte", "Ser influencer não te deu liberdade. Te deu um chefe novo: o algoritmo.",
         "Que muda sem avisar e não te deve nada. Você já sentiu isso?", "#algoritmo #instagram #influencer"),
        ("C · Salvamento", "O alcance orgânico do Instagram caiu em média 35%.",
         "Salva esse vídeo e lembra dele antes de colocar todas as fichas numa plataforma só.",
         "#alcanceorganico #instagram #marketingdigital"),
    ]),
    ("03", "O que o mercado compra hoje", "O que as marcas compram hoje", [
        ("A · Curiosidade", "As marcas pararam de comprar seguidores. Sabe o que elas compram agora?",
         "Quase 10 anos nesse mercado e eu vi essa virada acontecer.",
         "#marketingdeinfluencia #marcas #publi"),
        ("B · Opinião forte", "Relação vale mais do que vitrine.",
         "Uma conta que construiu confiança de verdade vale mais do que uma com milhões de seguidores "
         "que ninguém escuta. Concorda?", HASH_BASE),
        ("C · Compartilhamento", "Se você é criador, assiste antes da próxima negociação com marca.",
         "E manda pra quem ainda acha que número de seguidor é tudo.",
         "#criadordeconteudo #publi #negociacao"),
    ]),
    ("04", "Quem sobrevive x quem constrói", "Quem sobrevive x quem constrói", [
        ("A · Curiosidade", "Depois de quase 10 anos nesse mercado, eu diria que são 3 coisas.",
         "A terceira é a que mais gente erra.", "#influenciadordigital #negociodigital #creatoreconomy"),
        ("B · Opinião forte", "Nicho é categoria. Olhar é o que só você tem.",
         "Quem constrói tudo em uma plataforma só está construindo no terreno dos outros.",
         "#marcapessoal #criadordeconteudo #empreendedorismo"),
        ("C · Salvamento", "Salva: as 3 coisas que separam quem sobrevive de quem constrói.",
         "1. Ponto de vista próprio. 2. Não depender de uma plataforma. 3. Publi é renda, não modelo de "
         "negócio.", "#dicasparacriadores #influencer #negociodigital"),
    ]),
    ("05", "O que você está construindo?", "A pergunta que vale fazer hoje", [
        ("A · Curiosidade", "A pergunta que eu faria hoje se estivesse começando.",
         "E que vale pra quem tem 10 mil ou 1 milhão de seguidores.",
         "#influenciadordigital #criadordeconteudo #reflexao"),
        ("B · Provocação", "Quase 4 milhões de criadores só no Instagram. Você quer ser mais um?",
         "Me responde com sinceridade aqui nos comentários.", "#influencer #instagram #criadordeconteudo"),
        ("C · Conversa", "Não é “como eu cresço mais rápido”.",
         "É: o que você está construindo que vai continuar existindo independente do algoritmo de "
         "amanhã? Responde aqui, quero ler.", "#empreendedorismo #marcapessoal #influenciadordigital"),
    ]),
]


def cartao(rotulo, gancho, corpo, hashtags):
    etiqueta = Table([[Paragraph(rotulo.upper(), st["tag"])]], colWidths=[None])
    etiqueta.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), AMARELO),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                  ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    conteudo = [etiqueta, Spacer(1, 6), Paragraph(gancho, st["gancho"]), Spacer(1, 3),
                Paragraph(corpo, st["legenda"]), Spacer(1, 3),
                Paragraph("Episódio completo no YouTube: DEEP.", st["legenda"]), Spacer(1, 5),
                Paragraph(hashtags, st["nota"])]
    t = Table([[conteudo]], colWidths=[170 * mm])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINHA),
                           ("LINEBEFORE", (0, 0), (0, -1), 2.5, AMARELO_ESC),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return KeepTogether([t, Spacer(1, 8)])


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(AMARELO_ESC)
    canvas.rect(20 * mm, 12 * mm, 1.2 * mm, 5 * mm, stroke=0, fill=1)
    canvas.setFont("Medium", 7.5)
    canvas.setFillColor(SUAVE)
    canvas.drawString(23.5 * mm, 13.3 * mm, "D E E P  ·  S A M A R A   C H E C O N   —   legendas para Reels de teste")
    canvas.drawRightString(190 * mm, 13.3 * mm, str(doc.page))
    canvas.restoreState()


def main():
    doc = SimpleDocTemplate(SAIDA, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=20 * mm, bottomMargin=24 * mm,
                            title="DEEP — legendas para Reels de teste", author="DEEP")
    s = []
    s += [Paragraph("DEEP&nbsp;&nbsp;·&nbsp;&nbsp;SAMARA CHECON", st["capa_marca"]),
          Paragraph("Legendas para Reels de teste", st["capa_titulo"]),
          Paragraph("Episódio “Como ser influencer”: 5 cortes, 3 versões de legenda cada", st["capa_sub"]),
          Spacer(1, 14)]

    s.append(Paragraph("Como usar", st["h1"]))
    s.append(Paragraph("três ângulos diferentes para descobrir o que o seu público responde melhor", st["h1sub"]))
    for txt in [
        "<b>A · Curiosidade</b>: abre uma pergunta que só o vídeo responde. Segura quem está rolando o feed.",
        "<b>B · Opinião forte</b>: uma frase de posicionamento. Puxa comentários (concordo / discordo).",
        "<b>C · Compartilhamento ou salvamento</b>: pede uma ação clara (mandar pra alguém ou salvar). "
        "Envios e salvamentos são dos sinais que mais pesam na distribuição de um Reel.",
    ]:
        s.append(Paragraph(txt, st["item"], bulletText="•"))
    s.append(Spacer(1, 8))
    s.append(Paragraph("Como testar", st["h1"]))
    s.append(Paragraph("usando os Reels de teste do Instagram", st["h1sub"]))
    for txt in [
        "Publique o mesmo corte como <b>Reel de teste</b> (opção “Teste” antes de compartilhar): ele é mostrado "
        "primeiro para quem ainda não te segue. Use uma versão de legenda por teste.",
        "Espere <b>24 a 72 horas</b> e compare, na ordem: <b>compartilhamentos</b>, <b>salvamentos</b>, "
        "<b>visualizações de não seguidores</b> e <b>tempo médio assistido</b>. Curtidas pesam menos.",
        "A versão vencedora vai para o perfil. Se nenhuma se destacar, publique a A.",
        "Mude <b>só a legenda</b> entre os testes: mesmo vídeo, mesma capa, mesmo horário, para a comparação "
        "ser justa.",
    ]:
        s.append(Paragraph(txt, st["item"], bulletText="•"))
    s.append(Spacer(1, 8))
    s.append(Paragraph("Boas práticas em todas as versões", st["h1"]))
    s.append(Spacer(1, 4))
    for txt in [
        "A <b>primeira linha</b> é o gancho: é o que aparece antes do “mais”. Curta e direta.",
        "Termos que as pessoas pesquisam (<i>como ser influencer</i>, <i>influenciador digital</i>, "
        "<i>publi</i>) ajudam o Reel a aparecer na busca do Instagram.",
        "<b>3 a 5 hashtags</b> relevantes são suficientes.",
        "Link do episódio completo na bio e num <b>comentário fixado</b>.",
        "Os números usados são os que a Samara fala no vídeo. Se tiver a fonte das pesquisas, vale citar.",
    ]:
        s.append(Paragraph(txt, st["item"], bulletText="•"))

    for num, nome, gancho_video, versoes in CORTES:
        s.append(PageBreak())
        s.append(Paragraph(f"Corte {num} — {nome}", st["h1"]))
        s.append(Paragraph(f"título na tela: “{gancho_video}”", st["h1sub"]))
        for rotulo, gancho, corpo, hashtags in versoes:
            s.append(cartao(rotulo, gancho, corpo, hashtags))
    doc.build(s, onFirstPage=rodape, onLaterPages=rodape)


if __name__ == "__main__":
    main()
