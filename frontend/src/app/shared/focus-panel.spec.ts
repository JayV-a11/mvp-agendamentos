import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { FocusPanel } from './focus-panel';

@Component({
  imports: [FocusPanel],
  template: '<h2 appFocusPanel tabindex="-1">Editar serviço</h2>',
})
class Host {}

describe('Foco em formulário aberto', () => {
  it('move foco para o título após renderizar e rola quando o navegador oferece suporte', async () => {
    const scroll = vi.fn();
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scroll,
    });
    const fixture = TestBed.createComponent(Host);
    fixture.detectChanges();
    await fixture.whenStable();
    expect(document.activeElement).toBe(fixture.nativeElement.querySelector('h2'));
    expect(scroll).toHaveBeenCalledWith({ block: 'nearest' });
    delete (HTMLElement.prototype as Partial<HTMLElement>).scrollIntoView;
  });
  it('mantém foco em ambientes de teste sem scrollIntoView', async () => {
    const fixture = TestBed.createComponent(Host);
    fixture.detectChanges();
    await fixture.whenStable();
    expect(document.activeElement).toBe(fixture.nativeElement.querySelector('h2'));
  });
});
