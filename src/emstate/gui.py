"""Editor e simulador gráfico da linguagem EmState."""

from pathlib import Path
from zipfile import ZipFile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .codegen import ArduinoGenerator, CCodeGenerator
from .lexer import Lexer, LexerError
from .parser import Parser, ParserError
from .semantic import SemanticAnalyzer, SemanticError
from .simulator import Simulator
from .visualizer import StateMachineVisualizer


EXEMPLOS = Path(__file__).resolve().parents[2] / "examples"
ARQUIVOS = [("Programa EmState", "*.ems"), ("Todos os arquivos", "*.*")]


class Interface:
    def __init__(self, janela):
        self.janela = janela
        janela.title("EmState • Editor e simulador")
        janela.geometry("1060x690")
        janela.minsize(760, 520)
        self.original = ""
        self.validado = None
        self.sim = None
        self.nome = tk.StringVar(value="Programa.ems")
        self.status = tk.StringVar()
        self.estado = tk.StringVar()
        self.regra = tk.StringVar()

        topo = tk.Frame(janela, bg="#173b43", padx=20, pady=12)
        topo.pack(fill="x")
        tk.Label(topo, text="EmState", bg="#173b43", fg="white",
                 font=("Inter", 20, "bold")).pack(side="left")
        tk.Label(topo, text="Editor e simulador", bg="#173b43", fg="#c1e4dc",
                 padx=14).pack(side="left")
        barra = ttk.Frame(janela, padding=(16, 10))
        barra.pack(fill="x")
        ttk.Button(barra, text="Abrir arquivo…", command=self.abrir).pack(side="left")
        exemplos = sorted(EXEMPLOS.glob("*.ems"))
        if exemplos:
            botao = ttk.Menubutton(barra, text="Exemplos ▾")
            menu = tk.Menu(botao, tearoff=False)
            for caminho in exemplos:
                menu.add_command(label=caminho.stem.replace("_", " ").capitalize(),
                                 command=lambda p=caminho: self.carregar(p))
            botao.configure(menu=menu)
            botao.pack(side="left", padx=6)
        ttk.Button(barra, text="Salvar como…", command=self.salvar).pack(side="left")
        exportar = ttk.Menubutton(barra, text="Exportar ▾")
        formatos = tk.Menu(exportar, tearoff=False)
        for titulo, extensao in [("Projeto C (.zip)", ".zip"), ("Arduino (.ino)", ".ino"),
                                 ("Diagrama Mermaid (.mmd)", ".mmd"), ("Diagrama Graphviz (.dot)", ".dot")]:
            formatos.add_command(label=titulo, command=lambda ext=extensao: self.exportar(ext))
        exportar.configure(menu=formatos)
        exportar.pack(side="left", padx=6)
        ttk.Label(barra, textvariable=self.nome).pack(side="right")

        paineis = ttk.Panedwindow(janela, orient="horizontal")
        paineis.pack(fill="both", expand=True, padx=12)
        esquerda = ttk.Frame(paineis, padding=8)
        direita = ttk.Frame(paineis, padding=8)
        paineis.add(esquerda, weight=1)
        paineis.add(direita, weight=1)
        ttk.Label(esquerda, text="Programa", font=("Inter", 14, "bold")).pack(anchor="w")
        self.editor = ScrolledText(esquerda, width=42, height=12, undo=True,
                                   bg="#142b32", fg="#edf6f2", insertbackground="white",
                                   font=("Consolas", 10), padx=10, pady=10, wrap="word")
        self.editor.pack(fill="both", expand=True, pady=8)
        self.editor.tag_configure("erro", background="#833e39")
        self.editor.bind("<<Modified>>", self.editado)
        ttk.Button(esquerda, text="Verificar programa", command=self.verificar).pack(anchor="w")

        ttk.Label(direita, text="Simulação", font=("Inter", 14, "bold")).pack(anchor="w")
        ttk.Label(direita, textvariable=self.estado, foreground="#12645f",
                  font=("Inter", 13, "bold")).pack(anchor="w", pady=(12, 2))
        ttk.Label(direita, textvariable=self.regra, wraplength=335,
                  justify="left").pack(fill="x", pady=(0, 10))
        self.entradas = ttk.LabelFrame(direita, text="Entradas do ciclo", padding=8)
        self.entradas.pack(fill="x")
        controles = ttk.Frame(direita)
        controles.pack(fill="x", pady=10)
        self.avancar = ttk.Button(controles, text="Avançar um ciclo", command=self.passo)
        self.avancar.pack(side="left")
        ttk.Button(controles, text="Reiniciar", command=self.verificar).pack(side="left", padx=6)
        ttk.Label(direita, text="Histórico de execução").pack(anchor="w")
        self.log = ScrolledText(direita, state="disabled", height=5, width=36,
                                wrap="word", padx=8, pady=6)
        self.log.pack(fill="both", expand=True, pady=6)
        ttk.Label(janela, textvariable=self.status, wraplength=740,
                  padding=(20, 8)).pack(fill="x")
        janela.protocol("WM_DELETE_WINDOW", self.fechar)
        inicial = EXEMPLOS / "semaforo.ems"
        if inicial.is_file():
            self.carregar(inicial)
        else:
            self.substituir("sistema Luz\nestado APAGADA\nestado ACESA\n\n"
                            "APAGADA -> ACESA quando botao pressionado\n"
                            "ACESA -> APAGADA quando botao solto\n", "Luz.ems")

    def codigo(self):
        return self.editor.get("1.0", "end-1c")

    def permitir_troca(self):
        if self.codigo() == self.original:
            return True
        escolha = messagebox.askyesnocancel("Programa alterado", "Salvar suas alterações?")
        return escolha is False or (escolha is True and self.salvar())

    def fechar(self):
        if self.permitir_troca():
            self.janela.destroy()

    def abrir(self):
        nome = filedialog.askopenfilename(filetypes=ARQUIVOS)
        if nome:
            self.carregar(Path(nome))

    def carregar(self, caminho):
        try:
            texto = caminho.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as erro:
            messagebox.showerror("Falha ao abrir", str(erro))
            return
        if self.permitir_troca():
            self.substituir(texto, caminho.name)

    def substituir(self, texto, nome):
        self.original = texto
        self.nome.set(nome)
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", texto)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.verificar()

    def salvar(self):
        nome = filedialog.asksaveasfilename(initialfile=self.nome.get(),
                                            defaultextension=".ems", filetypes=ARQUIVOS)
        if not nome:
            return False
        texto = self.codigo()
        try:
            Path(nome).write_text(texto, encoding="utf-8")
        except OSError as erro:
            messagebox.showerror("Falha ao salvar", str(erro))
            return False
        self.original = texto
        self.nome.set(Path(nome).name)
        return True

    def exportar(self, extensao):
        if self.validado != self.codigo():
            self.verificar()
        if self.sim is None:
            return
        ast = self.sim.ast
        base = ast.nome_sistema
        nome = filedialog.asksaveasfilename(initialfile=base + extensao, defaultextension=extensao,
                                            filetypes=[("Arquivo gerado", "*" + extensao)])
        if not nome:
            return
        try:
            if extensao == ".zip":
                gerador = CCodeGenerator(ast, self.tabela)
                with ZipFile(nome, "w") as pacote:
                    pacote.writestr(base + ".h", gerador.generate_header())
                    pacote.writestr(base + ".c", gerador.generate_source())
                    pacote.writestr("simulacao_" + base + ".c", gerador.generate_simulation_main())
            else:
                if extensao == ".ino":
                    conteudo = ArduinoGenerator(ast, self.tabela).generate_sketch()
                elif extensao == ".mmd":
                    conteudo = self.visualizador.to_mermaid()
                else:
                    conteudo = self.visualizador.to_dot()
                Path(nome).write_text(conteudo, encoding="utf-8")
        except OSError as erro:
            messagebox.showerror("Falha ao exportar", str(erro))
            return
        self.status.set(f"Arquivo exportado em {nome}")

    def editado(self, evento):
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            if self.validado != self.codigo():
                self.avancar.state(["disabled"])
                self.status.set("Programa alterado. Clique em Verificar programa para simular.")
                self.editor.tag_remove("erro", "1.0", "end")
                self.validado = None

    def verificar(self):
        codigo = self.codigo()
        self.editor.tag_remove("erro", "1.0", "end")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        for widget in self.entradas.winfo_children():
            widget.destroy()
        try:
            ast = Parser(Lexer(codigo).tokenize()).parse()
            analise = SemanticAnalyzer()
            tabela = analise.analyze(ast)
        except (LexerError, ParserError, SemanticError) as erro:
            self.sim = self.validado = None
            self.avancar.state(["disabled"])
            self.estado.set("Aguardando correção")
            self.regra.set("")
            self.status.set(str(erro))
            self.editor.tag_add("erro", f"{erro.line}.0", f"{erro.line}.end")
            self.editor.see(f"{erro.line}.0")
            return
        self.validado = codigo
        self.tabela = tabela
        self.sim = Simulator(ast)
        self.visualizador = StateMachineVisualizer(ast)
        self.numeros = {}
        self.eventos = {}
        for nome in tabela.variaveis_sensores:
            valor = tk.StringVar(value="0")
            self.numeros[nome] = valor
            self.campo(nome, ttk.Entry(self.entradas, textvariable=valor))
        for nome, simbolo in tabela.dispositivos.items():
            if simbolo.metadata["tipo"] == "sensor":
                opcoes = ["Sem evento"] + sorted(simbolo.metadata["comandos"])
                valor = tk.StringVar(value=opcoes[0])
                self.eventos[nome] = valor
                self.campo(nome, ttk.Combobox(self.entradas, state="readonly",
                                              textvariable=valor, values=opcoes))
        if not self.numeros and not self.eventos:
            ttk.Label(self.entradas, text="Este programa avança sem sensores.").pack()
        self.avancar.state(["!disabled"])
        self.atualizar_estado()
        self.status.set(f"{ast.nome_sistema} • Programa válido • {len(self.sim.estados)} estados")
        for aviso in analise.warnings:
            self.registrar(str(aviso))

    def campo(self, nome, widget):
        linha = self.entradas.grid_size()[1]
        ttk.Label(self.entradas, text=nome).grid(row=linha, column=0, sticky="w", padx=4)
        widget.grid(row=linha, column=1, sticky="ew", padx=4, pady=2)
        self.entradas.columnconfigure(1, weight=1)

    def atualizar_estado(self):
        atual = self.sim.estado_atual
        self.estado.set(f"{atual}   ·   Ciclo {self.sim.ciclo}")
        regras = []
        for trans in self.sim.transicoes_por_estado.get(atual, []):
            cond = self.visualizador._condicao_str(trans.condicao)
            regras.append(f"Vai para {trans.destino} " + (f"quando {cond}." if cond else "no próximo ciclo."))
        self.regra.set("\n".join(regras) or "Este estado não tem transições de saída.")

    def registrar(self, texto):
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def passo(self):
        if self.validado != self.codigo() or self.sim is None:
            return
        valores = {}
        for nome, campo in self.numeros.items():
            try:
                valores[nome] = float(campo.get().replace(",", "."))
            except ValueError:
                messagebox.showerror("Valor inválido", f"Digite um número no campo {nome}.")
                return
        for nome, valor in valores.items():
            self.sim.set_variavel(nome, valor)
        for nome, campo in self.eventos.items():
            if campo.get() == "Sem evento":
                self.sim.clear_evento_dispositivo(nome)
            else:
                self.sim.set_evento_dispositivo(nome, campo.get())
        resultado = self.sim.step()
        origem = resultado["estado_anterior"]
        destino = resultado["estado_atual"]
        movimento = f"{origem} → {destino}" if resultado["transicao"] else f"Permaneceu em {origem}"
        acoes = ", ".join(resultado["acoes"]) or "nenhuma"
        self.registrar(f"Ciclo {self.sim.ciclo}   ·   {movimento}\nAções em {origem}: {acoes}")
        self.atualizar_estado()


def main():
    janela = tk.Tk()
    Interface(janela)
    janela.mainloop()
