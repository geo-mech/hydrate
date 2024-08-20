function image = image_data(x1, y1, x2, y2, data)

image = data;
[image(:,1), image(:,2)] = symmetric_point_about_line(x1, y1, x2, y2, image(:,1), image(:,2));

end 
