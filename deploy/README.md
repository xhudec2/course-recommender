### Deployment on a VM through Oracle Cloud

Templates in this directory:
- [course-recommender.service](course-recommender.service)
- [course-recommender.env.example](course-recommender.env.example)
- [cloudflared-config.yml.example](cloudflared-config.yml.example)

Steps to deploy:
1. Install `ollama` and `uv` on the VM. Run `ollama signin` and `ollama pull mxbai-embed-large:335m`.
2. Copy this project to the VM and run `uv sync`.
3. Put the env file at `/etc/course-recommender.env` (chmod `600`) with `CHAT_API_KEY` set, matching the value the frontend proxy sends.
4. Copy `deploy/course-recommender.service` to `/etc/systemd/system/course-recommender.service`, adjusting `User`/`WorkingDirectory` for your VM's username.
5. `sudo systemctl daemon-reload && sudo systemctl enable --now course-recommender`, then `sudo journalctl -u course-recommender -f` to confirm it's healthy.
6. Expose it with a cloudflare tunnel
   ```sh
   cloudflared tunnel login
   cloudflared tunnel create course-recommender
   # fill in deploy/cloudflared-config.yml.example with the printed tunnel UUID and save as ~/.cloudflared/config.yml
   cloudflared tunnel route dns course-recommender api.your-domain.com
   sudo cloudflared --config /home/<user>/.cloudflared/config.yml service install
   sudo systemctl enable --now cloudflared
   ```
