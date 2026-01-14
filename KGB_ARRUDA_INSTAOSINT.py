import requests
import json
import os
import sys
import logging
import time
from datetime import datetime
from collections import Counter
from fpdf import FPDF
from typing import Optional, Dict, List, Tuple

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class PDFReport(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_font("helvetica", size=10)

    def safe_text(self, text):
        if not text: return ""
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    def header(self):
        if self.page_no() == 1:
            self.set_font('helvetica', 'B', 16)
            self.set_text_color(63, 81, 181)
            self.cell(0, 15, self.safe_text('RELATÓRIO DE INVESTIGAÇÃO'), 0, 1, 'C')
            self.set_draw_color(63, 81, 181)
            self.line(10, 25, 200, 25)
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, self.safe_text(f'Página {self.page_no()} | Gerado em Instagram Scrapper KGB_Arruda {timestamp} |'), 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, self.safe_text(title), 0, 1, 'L', True)
        self.ln(4)


class InstagramInvestigatorV4:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
            "x-ig-app-id": "936619743392459"
        }
        self.temp_dir = "temp_images"
        os.makedirs(self.temp_dir, exist_ok=True)

    def _download_image(self, url: str, name: str) -> Optional[str]:
        if not url: return None
        try:
            path = os.path.join(self.temp_dir, f"{name}.jpg")
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(response.content)
                return path
        except Exception as e:
            logger.error(f"Erro ao baixar imagem: {e}")
        return None

    def get_followers_set(self, user_id: str, session_id: str, count: int = 50) -> set:
        """Nova Função: Obtém um conjunto de usernames de seguidores para análise de interseção"""
        url = f'https://i.instagram.com/api/v1/friendships/{user_id}/followers/?count={count}'
        try:
            resp = self.session.get(url, headers=self.headers, cookies={'sessionid': session_id}, timeout=20)
            users = resp.json().get("users", [])
            return {u.get("username") for u in users}
        except:
            return set()

    def perform_graph_analysis(self, target_id: str, target_followers: set, top_interactors: list,
                               session_id: str) -> list:
        """Nova Função: Realiza a Análise de Grafos (Interseção de Seguidores)"""
        logger.info(f"Iniciando Graph Analysis em {len(top_interactors)} interatores...")
        graph_results = []

        # Analisar os top 5 interatores para evitar excesso de requests
        for username, count in top_interactors[:5]:
            try:
                # 1. Obter ID do interator
                url_id = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
                resp_id = self.session.get(url_id, headers=self.headers, cookies={'sessionid': session_id}, timeout=20)
                interactor_id = resp_id.json()["data"]["user"]["id"]

                # 2. Obter seguidores do interator
                interactor_followers = self.get_followers_set(interactor_id, session_id, count=100)

                # 3. Calcular Interseção
                common = target_followers.intersection(interactor_followers)

                graph_results.append({
                    "username": username,
                    "interactions": count,
                    "common_count": len(common),
                    "common_users": list(common)[:10]  # Top 10 comuns
                })
                time.sleep(1.5)  # Delay para evitar block
            except:
                continue
        return graph_results

    def get_user_data(self, username: str, session_id: str) -> Optional[Dict]:
        cookies = {'sessionid': session_id}
        url_profile = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'

        try:
            # 1. Perfil Básico
            resp = self.session.get(url_profile, headers=self.headers, cookies=cookies, timeout=30)
            if resp.status_code != 200:
                logger.error(f"Erro ao acessar perfil: {resp.status_code}")
                return None

            raw_data = resp.json()["data"]["user"]
            user_id = raw_data["id"]

            # Info detalhada
            url_info = f'https://i.instagram.com/api/v1/users/{user_id}/info/'
            info_resp = self.session.get(url_info, headers=self.headers, cookies=cookies, timeout=30)
            profile_info = info_resp.json().get("user", raw_data)

            profile_pic_url = profile_info.get("hd_profile_pic_url_info", {}).get("url") or profile_info.get(
                "profile_pic_url")
            profile_pic_path = self._download_image(profile_pic_url, f"profile_{username}")

            # 2. Feed (10 posts)
            url_feed = f'https://i.instagram.com/api/v1/feed/user/{user_id}/'
            feed_resp = self.session.get(url_feed, headers=self.headers, cookies=cookies, timeout=30)
            items = feed_resp.json().get("items", [])[:10]

            posts_data = []
            interaction_counter = Counter()
            all_recent_comments = []

            for idx, item in enumerate(items):
                # Imagem do post
                image_versions = item.get("image_versions2", {}).get("candidates", [])
                post_img_url = image_versions[0].get("url") if image_versions else None
                post_img_path = self._download_image(post_img_url, f"post_{username}_{idx}")

                post_info = {
                    "id": item.get("id"),
                    "url": f"https://www.instagram.com/p/{item.get('code')}/",
                    "caption": item.get("caption", {}).get("text", "Sem legenda") if item.get(
                        "caption") else "Sem legenda",
                    "location": item.get("location", {}).get("name", "Nenhuma"),
                    "lat": item.get("location", {}).get("lat"),
                    "lng": item.get("location", {}).get("lng"),
                    "timestamp": datetime.fromtimestamp(item.get("taken_at")).strftime('%d/%m/%Y %H:%M'),
                    "likes": item.get("like_count"),
                    "comments_count": item.get("comment_count"),
                    "local_img": post_img_path
                }
                posts_data.append(post_info)

                # Coleta de Comentários para Análise de Interação
                if item.get("comment_count", 0) > 0:
                    try:
                        comm_url = f'https://i.instagram.com/api/v1/media/{item.get("id")}/comments/'
                        comm_resp = self.session.get(comm_url, headers=self.headers, cookies=cookies, timeout=15)
                        comments = comm_resp.json().get("comments", [])

                        for c in comments:
                            commenter = c.get("user", {}).get("username")
                            interaction_counter[commenter] += 1
                            if len(all_recent_comments) < 30:
                                all_recent_comments.append({
                                    "user": commenter,
                                    "text": c.get("text"),
                                    "date": datetime.fromtimestamp(c.get("created_at")).strftime('%d/%m/%Y %H:%M')
                                })
                    except:
                        pass

                # Simular delay humano para evitar block
                time.sleep(1)

            # 3. Seguidores (Amostra maior para análise)
            url_followers = f'https://i.instagram.com/api/v1/friendships/{user_id}/followers/?count=100'
            followers_resp = self.session.get(url_followers, headers=self.headers, cookies=cookies, timeout=30)
            followers_list = followers_resp.json().get("users", [])
            target_followers_set = {u.get("username") for u in followers_list}

            # 4. Executar Graph Analysis (Nova Camada)
            top_interactors = interaction_counter.most_common(10)
            graph_intel = self.perform_graph_analysis(user_id, target_followers_set, top_interactors, session_id)

            return {
                "profile": profile_info,
                "profile_pic": profile_pic_path,
                "posts": posts_data,
                "recent_comments": all_recent_comments[:30],
                "top_interactors": top_interactors,
                "followers_sample": followers_list[:30],
                "graph_analysis": graph_intel
            }

        except Exception as e:
            logger.error(f"Erro crítico na coleta: {e}")
            return None

    def generate_pdf(self, data: Dict, filename: str):
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # 1. Resumo do Perfil
        pdf.chapter_title('1. RESUMO DO PERFIL ALVO')
        if data.get('profile_pic'):
            try:
                pdf.image(data['profile_pic'], x=150, y=35, w=40)
            except:
                pass

        p = data['profile']
        # Expansão solicitada: Incluindo todas as informações possíveis no Tópico 1
        fields = [
            ('Username', f"@{p.get('username')}"),
            ('Nome Completo', p.get('full_name')),
            ('User ID (PK)', p.get('pk')),
            ('Biografia', p.get('biography', 'N/A')),
            ('Link Externo', p.get('external_url', 'Nenhum')),
            ('Seguidores', f"{p.get('follower_count', 0):,}"),
            ('Seguindo', f"{p.get('following_count', 0):,}"),
            ('Total de Posts', f"{p.get('media_count', 0):,}"),
            ('Privado', 'Sim' if p.get('is_private') else 'Não'),
            ('Verificado', 'Sim' if p.get('is_verified') else 'Não'),
            ('Conta Comercial', 'Sim' if p.get('is_business') else 'Não'),
            ('Categoria', p.get('category', 'N/A')),
            ('Email Público', p.get('public_email', 'N/A')),
            ('Telefone Público', p.get('contact_phone_number', 'N/A')),
            ('Cidade', p.get('city_name', 'N/A')),
            ('Endereço', p.get('address_street', 'N/A'))
        ]
        for label, value in fields:
            pdf.set_font('helvetica', 'B', 10)
            pdf.cell(40, 7, pdf.safe_text(f"{label}:"), 0, 0)
            pdf.set_font('helvetica', '', 10)
            pdf.multi_cell(100, 7, pdf.safe_text(str(value)), 0, 'L')

        # 2. Graph Analysis (Nova Seção)
        pdf.ln(10)
        pdf.chapter_title('2. GRAPH ANALYSIS (CÍRCULOS DE CONFIANÇA)')
        pdf.set_font('helvetica', 'I', 9)
        pdf.multi_cell(0, 5, pdf.safe_text(
            "Análise de interseção entre os seguidores do alvo e seus principais interatores. Números altos indicam proximidade real ou contas de suporte."))
        pdf.ln(3)

        if not data.get('graph_analysis'):
            pdf.cell(0, 6, "Dados insuficientes para análise de grafos.", 0, 1)
        else:
            for item in data['graph_analysis']:
                pdf.set_font('helvetica', 'B', 10)
                pdf.cell(0, 7, pdf.safe_text(f"Interator: @{item['username']} ({item['interactions']} interações)"), 0, 1)
                pdf.set_font('helvetica', '', 9)
                pdf.cell(0, 6, pdf.safe_text(f"Seguidores em Comum: {item['common_count']}"), 0, 1)
                if item['common_users']:
                    users_str = ", ".join(item['common_users'][:5])
                    pdf.set_font('helvetica', 'I', 8)
                    pdf.multi_cell(0, 5, pdf.safe_text(f"Amostra Comum: {users_str}..."))
                pdf.ln(2)

        # 3. Top 30 Seguidores que mais interagem
        pdf.ln(5)
        pdf.chapter_title('3. TOP INTERATORES (RANKING)')
        pdf.set_font('helvetica', '', 9)
        if not data['top_interactors']:
            pdf.cell(0, 6, "Nenhuma interação detectada.", 0, 1)
        else:
            col_width = 60
            count = 0
            for user, interactions in data['top_interactors']:
                text = f"@{user} ({interactions}x)"
                pdf.cell(col_width, 6, pdf.safe_text(text), 0, 0)
                count += 1
                if count % 3 == 0: pdf.ln(6)
            if count % 3 != 0: pdf.ln(6)

        # 4. Últimos 30 Comentários
        pdf.ln(5)
        pdf.chapter_title('4. ÚLTIMOS 30 COMENTÁRIOS COLETADOS')
        pdf.set_font('helvetica', '', 8)
        for c in data['recent_comments']:
            pdf.set_font('helvetica', 'B', 8)
            pdf.write(5, pdf.safe_text(f"@{c['user']} [{c['date']}]: "))
            pdf.set_font('helvetica', '', 8)
            pdf.write(5, pdf.safe_text(f"{c['text']}\n"))
            pdf.ln(2)

        # 5. Análise de 10 Posts com Imagens
        pdf.add_page()
        pdf.chapter_title('5. ANÁLISE DETALHADA DOS ÚLTIMOS 10 POSTS')

        for post in data['posts']:
            if pdf.get_y() > 200: pdf.add_page()
            start_y = pdf.get_y()

            pdf.set_font('helvetica', 'B', 9)
            pdf.cell(0, 6, pdf.safe_text(
                f"Data: {post['timestamp']} | Likes: {post['likes']} | Comentários: {post['comments_count']}"), 0, 1)

            pdf.set_font('helvetica', 'U', 8)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(0, 5, pdf.safe_text(f"Link: {post['url']}"), 0, 1, link=post['url'])
            pdf.set_text_color(0, 0, 0)

            pdf.set_font('helvetica', 'I', 8)
            loc = post['location']
            if post['lat']: loc += f" (Lat: {post['lat']}, Lng: {post['lng']})"
            pdf.cell(120, 5, pdf.safe_text(f"Local: {loc}"), 0, 1)

            pdf.set_font('helvetica', '', 8)
            caption = post['caption'][:250] + "..." if len(post['caption']) > 250 else post['caption']
            pdf.multi_cell(120, 4, pdf.safe_text(f"Legenda: {caption}"))

            if post.get('local_img'):
                try:
                    pdf.image(post['local_img'], x=140, y=start_y, w=50)
                except:
                    pass

            pdf.ln(15)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        pdf.output(filename)
        # Limpeza
        for f in os.listdir(self.temp_dir):
            try:
                os.remove(os.path.join(self.temp_dir, f))
            except:
                pass
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
        return filename

    def run(self):
        print(f"{Colors.OKGREEN}{Colors.BOLD}💀💀💀💀 Instagram Scrapper KGB_Arruda 💀💀💀💀{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}💀............................................ 💀{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}💀💀👮ferramenta OSINT COM API DO INSTAGRAM  💀💀{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}💀💀💀💀..DEV: arrudacibersec@proton.me 💀💀💀💀{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀{Colors.ENDC}")
        username = input("Username (sem @): ").strip().lstrip('@')
        session_id = input("Session ID: ").strip()

        if not username or not session_id:
            print(f"{Colors.FAIL}Erro: Dados incompletos.{Colors.ENDC}")
            return

        print(f"{Colors.OKCYAN}Iniciando Deep Scan + Graph Analysis de @{username}...{Colors.ENDC}")
        print(
            f"{Colors.WARNING}Aviso: Esta análise é profunda e levará cerca de 45-60 segundos para evitar bloqueios.{Colors.ENDC}")

        data = self.get_user_data(username, session_id)

        if data:
            filename = f"relatorio_graph_{username}.pdf"
            try:
                self.generate_pdf(data, filename)
                print(f"\n{Colors.OKGREEN}Investigação e Análise de Grafos concluídas!{Colors.ENDC}")
                print(f"{Colors.BOLD}Relatório gerado: {os.path.abspath(filename)}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.FAIL}Erro ao gerar PDF: {e}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}Falha ao coletar dados. Verifique o Session ID ou conexão.{Colors.ENDC}")


if __name__ == "__main__":
    investigator = InstagramInvestigatorV4()
    investigator.run()
