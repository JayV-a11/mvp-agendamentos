import { Component, ElementRef, viewChild } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  imports: [RouterOutlet],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  readonly content = viewChild.required<ElementRef<HTMLElement>>('content');

  skipToContent(event: Event) {
    event.preventDefault();
    this.content().nativeElement.focus();
  }
}
