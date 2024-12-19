package user

import (
	"encoding/json"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"io"
	"kth_activities_helper/internal/config"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"kth_activities_helper/internal/security"
	"log/slog"
	"net/http"
	url2 "net/url"
	"strconv"
	"strings"
	"time"
)

type DiscordOAuthResponse struct {
	resp.Response
	Username  string `json:"username"`
	DiscordId string `json:"discord_id"`
}

type UserSelectorEditor interface {
	SelectOneUser(osuId uint64) (models.User, error)
	EditUser(osuId uint64, discordId uint64, rating uint32, username string, active bool) (models.User, error)
}

func GetDiscordCode(log *slog.Logger, userSelectorEditor UserSelectorEditor) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.get.GetOne"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)
		// checking for props from http.Context and for user existence
		props, ok := r.Context().Value("props").(*security.Claims)
		if !ok {
			localLog.Error("Failed to do discordOauth because of context")
			render.JSON(w, r, resp.Error("Failed to do discord OAuth"))
			return
		}
		localLog.Info("props: ", props.OsuUserID, props.DiscordUserId)
		user, err := userSelectorEditor.SelectOneUser(props.OsuUserID)
		if err != nil {
			localLog.Error("Failed to do discordOauth because user does not exist")
			render.JSON(w, r, resp.Error("Failed to do discord OAuth"))
			http.Error(w, http.StatusText(404), 404)
			return
		}
		// PART 0: GETTING CODE
		var queryResults = r.URL.Query()
		if len(queryResults) != 1 {
			// http.Error(w, http.StatusText(400), 400)
			http.Redirect(w, r, "http://localhost:3000/users", 302)
			return
		}
		var code = queryResults.Get("code")
		localLog.Info("Got code", slog.String("code", code))

		// PART 1: getting token
		var apiUrl = "https://discord.com"
		var resource = "/api/v10/oauth2/token"
		data := url2.Values{}
		data.Set("client_id", config.AppConfig.OAuthConfig.DiscordClientId)
		data.Set("client_secret", config.AppConfig.OAuthConfig.DiscordClientSecret)
		data.Set("grant_type", "authorization_code")
		data.Set("code", code)
		data.Set("redirect_uri", "http://localhost:8089/api/discord")

		u, _ := url2.ParseRequestURI(apiUrl)
		u.Path = resource
		urlStr := u.String()
		client := &http.Client{}
		req, err := http.NewRequest(http.MethodPost, urlStr, strings.NewReader(data.Encode()))
		if err != nil {
			localLog.Error("Something bad happened with post request")
			return
		}
		req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
		response, err := client.Do(req)
		/* defer response.Body.Close()
		body, err := io.ReadAll(response.Body)
		var dataRead map[string]interface{}
		json.Unmarshal(body, &dataRead) */
		if err != nil {
			localLog.Error("Something bad happened with post request", err)
			// http.Error(w, http.StatusText(500), 500)
			http.Redirect(w, r, "http://localhost:3000/users", 302)
			return
		}
		defer response.Body.Close()
		body, err := io.ReadAll(response.Body)
		var dataRead map[string]interface{}
		err = json.Unmarshal(body, &dataRead)
		if err != nil {
			return
		}
		if response.StatusCode != 200 {
			localLog.Error("Something bad when accessing ", slog.String(urlStr, "url"))
			// http.Error(w, http.StatusText(500), 500)
			http.Redirect(w, r, "http://localhost:3000/users", 302)
			return
		}

		// PART2: GOT ACCESS TOKEN DISCORD, getting user info
		accessToken := dataRead["access_token"].(string)
		apiUrl = "https://discord.com"
		resource = "/api/v10/users/@me"

		u, _ = url2.ParseRequestURI(apiUrl)
		u.Path = resource
		urlStr = u.String()
		req, _ = http.NewRequest(http.MethodGet, urlStr, nil)
		req.Header.Add("Authorization", "Bearer "+accessToken)
		response, err = client.Do(req)
		if err != nil {
			localLog.Error("Something bad happened with GET request")
			// http.Error(w, http.StatusText(500), 500)
			http.Redirect(w, r, "http://localhost:3000/users", 302)
			return
		}
		defer response.Body.Close()
		body, _ = io.ReadAll(response.Body)
		err = json.Unmarshal(body, &dataRead)
		if err != nil {
			// http.Error(w, http.StatusText(500), 500)
			http.Redirect(w, r, "http://localhost:3000/users", 302)
			return
		}
		if response.StatusCode != 200 {
			localLog.Error("Something bad when accessing ", slog.String(urlStr, "url"))
			// http.Error(w, http.StatusText(500), 500)
			http.Redirect(w, r, "http://localhost:3000/users", 302)
			return
		}
		discordId := dataRead["id"].(string)
		discordIdUint, err := strconv.ParseUint(discordId, 10, 64)
		if err != nil {
			localLog.Error("Something bad happened with discordId")
			http.Redirect(w, r, "http://localhost:3000/users", 302)
			return
		}
		// username := dataRead["username"].(string)
		user, err = userSelectorEditor.EditUser(user.OsuId, discordIdUint, user.Rating, user.Username, user.Active)
		if err != nil {
			localLog.Error("Something bad when editing user ", slog.String(discordId, "discordIdUint"))
			http.Error(w, http.StatusText(500), 500)
			http.Redirect(w, r, "http://localhost:3000/users", 302)
			return
		}

		accessTokenOurDb, err := security.GenerateToken(&user, "access")
		if err != nil {
			localLog.Error("Failed to generate access token")
			render.JSON(w, r, resp.Error("Failed to generate access token"))
			return
		}
		security.SetCookie(w, "jwt-kth", accessTokenOurDb, int(time.Hour.Seconds()*2))
		http.Redirect(w, r, "http://localhost:3000/users", 302)
		return
	}
}
