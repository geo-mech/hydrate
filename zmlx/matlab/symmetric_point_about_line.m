function [xs, ys] = symmetric_point_about_line(x1, y1, x2, y2, xp, yp)
    % Calculate line coefficients Ax + By + C = 0
    A = y2 - y1;
    B = x1 - x2;
    C = x2 * y1 - x1 * y2;
    
    % Calculate distance from point (xp, yp) to line
    dist = abs(A * xp + B * yp + C) / sqrt(A^2 + B^2);
    
    % Calculate projection point (xt, yt)
    xt = xp - (A * (A * xp + B * yp + C)) / (A^2 + B^2);
    yt = yp - (B * (A * xp + B * yp + C)) / (A^2 + B^2);
    
    % Calculate symmetric point (xs, ys)
    xs = 2 * xt - xp;
    ys = 2 * yt - yp;
end
