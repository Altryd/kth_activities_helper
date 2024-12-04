package main

import (
	"fmt"
	"github.com/Altryd/osuParseMpLinks"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"kth_activities_helper/internal/config"
	"kth_activities_helper/internal/database"
	"kth_activities_helper/internal/http-server/handlers/match"
	"kth_activities_helper/internal/http-server/handlers/matchType"
	matchUser "kth_activities_helper/internal/http-server/handlers/matchUserScrim"
	"kth_activities_helper/internal/http-server/handlers/user"
	"kth_activities_helper/internal/security"
	"kth_activities_helper/internal/utility"
	"log/slog"
	"net/http"
	"os"
)

func AuthMiddleware(next http.Handler) http.Handler {
	fn := func(w http.ResponseWriter, r *http.Request) {
		// ctx := r.Context()
		jwt_token, err := r.Cookie("jwt-kth")
		//fmt.Println("cookie auth middleware: ", jwt_token, err)
		//fmt.Println("cookies: ", r.Cookies())
		// jwt_token, err := c.Cookie("jwt")
		if err != nil {
			w.WriteHeader(http.StatusUnauthorized)
			// c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			return
		}

		claims, err := security.ValidateToken(jwt_token.Value, "access")

		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
			// c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		// TODO: убрать принт ниже  остальные комменты после окончания тестирования
		fmt.Printf("\n[middleware] зашел пользователь с : osuid=%d ; discordId=%d\n", claims.OsuUserID, claims.DiscordUserId)
		// ctx.
		// ctx.v
		// c.Set("osuUserId", claims.OsuUserID)
		// c.Next()
		next.ServeHTTP(w, r)
	}
	return http.HandlerFunc(fn)
}

func main() {
	parsingConfig := osuParseMpLinks.ParsingConfig{Debug: true} // TODO: потом удалить, сейчас это нужно, чтобы зависимость не потерялась
	print(parsingConfig.Debug)
	config.Load()
	fmt.Println(config.AppConfig)

	log := setupLogger(config.AppConfig.Env)
	log.Info("Starting backend of kth_activities_helper...", slog.String("env", config.AppConfig.Env))

	storage, err := database.New(log)
	if err != nil {
		os.Exit(-1)
	}

	//id, err := storage.CreateMatchType("MeowMeowMeow")
	//if err != nil {
	//	os.Exit(-1)
	//}
	//log.Info("Inserted MatchType: ", slog.Uint64("id", id))

	router := chi.NewRouter()
	//middleware
	router.Use(middleware.RequestID)
	router.Use(middleware.Recoverer)
	router.Use(middleware.URLFormat)
	router.Use(cors.Handler(cors.Options{ // Чтобы с фронта можно POST послать
		// AllowedOrigins:   []string{"https://foo.com"}, // Use this to allow specific origin hosts
		// AllowedOrigins: []string{"http://localhost:3000", "https://localhost/*", "http://localhost:3000/*", "http://localhost:8089"},
		AllowedOrigins: []string{"http://localhost:3000", "http://localhost:3000", "http://localhost:8089"},
		// AllowOriginFunc:  func(r *http.Request, origin string) bool { return true },
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token", "Cookie"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		MaxAge:           33300, // Maximum value not ignored by any of major browsers
	}))

	router.With(AuthMiddleware).Get("/api/matches", match.GetAll(log, storage))
	// router.Get("/api/matches", match.GetAll(log, storage))
	router.Get("/api/matches/{id}", match.GetOne(log, storage))
	router.With(AuthMiddleware).Post("/api/match", match.New(log, storage))
	router.Put("/api/matches/{id}/edit", match.Edit(log, storage))
	router.Post("/api/matches/{id}/approve", match.Approve(log, storage))
	router.With(AuthMiddleware).Post("/api/parse_scrims", match.ParseMatches(log))

	router.Get("/api/create_pairs", match.CreatePairs(log, storage, storage))

	router.Get("/api/matchTypes", matchType.GetAll(log, storage))
	router.Post("/api/matchType", matchType.New(log, storage))

	router.Get("/api/users", user.GetAll(log, storage))
	router.Get("/api/users/{osuId}", user.GetOne(log, storage))
	router.Post("/api/user", user.New(log, storage))
	router.With(AuthMiddleware).Get("/api/me", user.GetMe(log, storage))
	router.Put("/api/matches/{osuId}/edit", user.EditUser(log, storage))
	router.Get("/api/discord", user.GetDiscordCode(log))
	router.Get("/api/oauth/osu", user.GetOsuCode(log, storage))

	router.Post("/api/match_user", matchUser.New(log, storage))
	matchTypes, err := storage.SelectMatchTypes()
	if err != nil {
		fmt.Printf("Error selecting match types: %v\n", err)
	} else {
		if len(matchTypes) == 0 {
			storage.CreateMatchType("scrim")
			storage.CreateMatchType("weekly")
		}
	}
	err = utility.UploadPlayers("internal/database/golang_players_dump.json", storage, log)
	if err != nil {
		fmt.Printf("Error uploading players: %s, skipping", err)
	}
	err = utility.UploadMatches("internal/database/golang_matches_dump.json", storage, log)
	if err != nil {
		fmt.Printf("Error uploading matches: %s, skipping", err)
	}
	err = utility.UploadMatchUserScrims("internal/database/golang_match_user_scrim_dump.json", storage, log)
	if err != nil {
		fmt.Printf("Error uploading matchUserScrims: %s, skipping", err)
	}

	srv := http.Server{
		Addr:              config.AppConfig.HTTPServer.Address,
		Handler:           router,
		ReadHeaderTimeout: config.AppConfig.HTTPServer.Timeout,
		WriteTimeout:      config.AppConfig.HTTPServer.Timeout,
		IdleTimeout:       config.AppConfig.HTTPServer.IdleTimeout,
	}

	if err := srv.ListenAndServe(); err != nil {
		log.Error("Failed to start server")
	}

	log.Error("Server stopped")
}

const (
	envLocal = "local"
	envDev   = "dev"
	envProd  = "prod"
)

func setupLogger(env string) *slog.Logger {
	var logger *slog.Logger

	switch env {
	case envLocal:
		logger = slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	case envDev:
		logger = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelDebug}))
	case envProd:
		logger = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	}

	return logger
}
