/**
 * O nível de leitura nos testes de seção. Chama o módulo `reading` importado estaticamente —
 * o mesmo que os componentes importaram, que guarda o nível corrente em memória.
 *
 * `comNivel(reading)` antes de montar; `limparNivel()` no `afterEach`.
 */
import { type Reading, resetReadingForTests, setReading } from "../src/reading";

export function comNivel(reading: Reading): void {
  setReading(reading);
}

export function limparNivel(): void {
  resetReadingForTests();
}
