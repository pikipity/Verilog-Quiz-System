`timescale 1ns/1ps

module tb_and2;
    reg a, b;
    wire y;

    and2 dut (
        .a(a),
        .b(b),
        .y(y)
    );

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_and2);
        
        $display("=== Test Start ===");
        
        #0 a=0; b=0;
        #1 $display("time=%0t a=%b b=%b y=%b", $time, a, b, y);
        
        #10 a=1; b=0;
        #1 $display("time=%0t a=%b b=%b y=%b", $time, a, b, y);
        
        #10 a=0; b=1;
        #1 $display("time=%0t a=%b b=%b y=%b", $time, a, b, y);
        
        #10 a=1; b=1;
        #1 $display("time=%0t a=%b b=%b y=%b", $time, a, b, y);
        
        #10 $display("=== Test End ===");
        $finish;
    end
endmodule
