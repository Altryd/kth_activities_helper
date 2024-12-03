package calculation

import (
	"math"
)

func GetNewRating(r0 float64, opponentsRating float64, winsFirst int, winsOpponent int, k ...int) float64 {
	kCoef := 35
	if len(k) > 0 {
		kCoef = k[0]
	}
	var G float64 = getG(winsFirst, winsOpponent)

	var W float64 = 0.5
	if winsFirst > winsOpponent {
		W = 1.0
	} else if winsFirst < winsOpponent {
		W = 0
	}
	var We float64 = getWe(r0, opponentsRating)
	return r0 + float64(kCoef)*G*(W-We)
}

func getG(winsFirst int, winsSecond int) float64 {
	var difference float64 = float64(winsFirst) - float64(winsSecond)
	if math.Abs(difference) <= 1.0 {
		return 1.0
	} else if math.Abs(difference) == 2.0 {
		return 3.0 / 2.0
	}
	return (11.0 + math.Abs(difference)) / 8.0
}

func getWe(ratingsFirst float64, ratingsSecond float64) float64 {
	dr := ratingsFirst - ratingsSecond
	denominator := math.Pow(10, -dr/400) + 1.0
	return 1 / denominator
}
