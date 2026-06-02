import { Component, inject, signal, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { ApiService } from './core/services/api.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements OnInit {
  private api = inject(ApiService);
  submitEnabled = signal(true);

  ngOnInit() {
    this.api.getConfig().subscribe(cfg => this.submitEnabled.set(cfg.submit_enabled));
  }
}
