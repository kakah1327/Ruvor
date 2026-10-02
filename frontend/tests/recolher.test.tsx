/**
 * O recolhimento (RF-06, RF-07 do M2.3; V-05): o `Collapsible`, que a seção Comportamento usa
 * para a assimetria e a curtose, e que a T10 repete na tabela dos modelos e na trilha.
 *
 * - fechado na iniciante, aberto na avançada; trocar o nível reaplica o padrão; abrir e fechar
 *   nos dois níveis, sem lembrar;
 * - o botão com `aria-expanded` e `aria-controls`, e o conteúdo fechado **fora da árvore** —
 *   não desenhado: a busca é pelo papel e pelo texto, e um conteúdo só escondido com `hidden`
 *   seria achado pelo texto;
 * - as marcas `data-collapsible` e `data-open`;
 * - nunca dentro de elemento com `aria-live`.
 *
 * O que é da seção (o histograma aberto, a prova por seção, os números iguais nos dois níveis)
 * fica em `ativo.test.tsx`, com a tela inteira.
 */
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { Collapsible } from "../src/components/Collapsible";
import { setReading } from "../src/reading";
import { comNivel, limparNivel } from "./nivel";

// O rótulo e o conteúdo de exemplo: os testes não dependem de `textos.ts`.
const LABEL = "Ver o conteúdo de exemplo";
const CONTENT = "O conteúdo recolhido de exemplo";

function renderCollapsible() {
  return render(
    <main>
      <p>Antes do recolhível</p>
      <Collapsible name="moments" label={LABEL}>
        <p>{CONTENT}</p>
      </Collapsible>
    </main>,
  );
}

const toggle = () => screen.getByRole("button", { name: LABEL });
const root = () =>
  document.querySelector<HTMLElement>('[data-collapsible="moments"]') as HTMLElement;

/** Fechado: o botão diz que não está expandido, e o conteúdo não existe — nem pelo texto. */
function expectClosed(): void {
  expect(toggle().getAttribute("aria-expanded")).toBe("false");
  expect(root().getAttribute("data-open")).toBe("false");
  expect(screen.queryByText(CONTENT)).toBeNull();
  const controls = toggle().getAttribute("aria-controls");
  expect(controls).toBeTruthy();
  expect(document.getElementById(controls as string)).toBeNull();
}

/** Aberto: o conteúdo existe, no elemento que o `aria-controls` aponta. */
function expectOpen(): void {
  expect(toggle().getAttribute("aria-expanded")).toBe("true");
  expect(root().getAttribute("data-open")).toBe("true");
  const content = screen.getByText(CONTENT);
  const controls = toggle().getAttribute("aria-controls") as string;
  const region = document.getElementById(controls);
  expect(region).not.toBeNull();
  expect(region?.contains(content)).toBe(true);
  expect(region?.hasAttribute("hidden")).toBe(false);
}

afterEach(() => {
  cleanup();
  limparNivel();
});

describe("V-05 — o padrão de cada nível", () => {
  it("nasce fechado na iniciante, sem nada guardado", () => {
    renderCollapsible();
    expectClosed();
  });

  it("nasce fechado na iniciante declarada", () => {
    comNivel("beginner");
    renderCollapsible();
    expectClosed();
  });

  it("nasce aberto na avançada", () => {
    comNivel("advanced");
    renderCollapsible();
    expectOpen();
  });

  it("o raiz leva data-collapsible com o nome, e o botão o rótulo, nos dois estados", () => {
    renderCollapsible();
    expect(root().getAttribute("data-collapsible")).toBe("moments");
    expect(toggle().textContent).toBe(LABEL);
    fireEvent.click(toggle());
    expect(toggle().textContent).toBe(LABEL);
  });
});

describe("V-05 — abrir e fechar, nos dois níveis", () => {
  it("na iniciante, abre e fecha pelo botão", () => {
    comNivel("beginner");
    renderCollapsible();
    fireEvent.click(toggle());
    expectOpen();
    fireEvent.click(toggle());
    expectClosed();
  });

  it("na avançada, fecha e abre pelo botão", () => {
    comNivel("advanced");
    renderCollapsible();
    fireEvent.click(toggle());
    expectClosed();
    fireEvent.click(toggle());
    expectOpen();
  });

  it("abrir não troca o nível nem é lembrado: montar de novo volta ao padrão", () => {
    comNivel("beginner");
    const { unmount } = renderCollapsible();
    fireEvent.click(toggle());
    expectOpen();
    expect(document.documentElement.dataset.reading).toBe("beginner");
    unmount();
    renderCollapsible();
    expectClosed();
  });
});

describe("V-05 — trocar o nível reaplica o padrão", () => {
  it("da iniciante para a avançada abre, e de volta fecha", () => {
    comNivel("beginner");
    renderCollapsible();
    expectClosed();
    act(() => setReading("advanced"));
    expectOpen();
    act(() => setReading("beginner"));
    expectClosed();
  });

  it("o aberto à mão na iniciante fecha ao voltar da avançada; o fechado à mão na avançada abre de novo", () => {
    comNivel("beginner");
    renderCollapsible();
    fireEvent.click(toggle());
    expectOpen();
    act(() => setReading("advanced"));
    fireEvent.click(toggle());
    expectClosed();
    act(() => setReading("beginner"));
    expectClosed();
    act(() => setReading("advanced"));
    expectOpen();
  });
});

describe("V-05 — fora de região viva", () => {
  it("nem o botão nem o raiz estão dentro de elemento com aria-live, aberto ou fechado", () => {
    comNivel("advanced");
    renderCollapsible();
    for (const open of [true, false]) {
      expect(root().closest("[aria-live]")).toBeNull();
      expect(root().querySelector("[aria-live]")).toBeNull();
      expect(toggle().closest("[aria-live]")).toBeNull();
      expect(root().getAttribute("data-open")).toBe(String(open));
      fireEvent.click(toggle());
    }
  });
});
