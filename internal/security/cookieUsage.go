package security

import (
	"net/http"
)

func SetCookie(w http.ResponseWriter, name string, value string, expirationSecond int) {
	cookie := buildCookie(name, value, expirationSecond)
	// req.AddCookie(cookie)
	http.SetCookie(w, cookie)
	// http.SetCookie(c.Writer, cookie)
}

func ClearCookie(w http.ResponseWriter, name string) {
	cookie := buildCookie(name, "", -1)
	// req.AddCookie(cookie)
	http.SetCookie(w, cookie)
	// http.SetCookie(c.Writer, cookie)
}

func buildCookie(name string, value string, expires int) *http.Cookie {
	cookie := &http.Cookie{
		Name:     name,
		Value:    value,
		Path:     "/",
		Domain:   "",
		HttpOnly: true,
		MaxAge:   expires,
		Secure:   true,
		SameSite: http.SameSiteNoneMode,
	}

	return cookie
}
